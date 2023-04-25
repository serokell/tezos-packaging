#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2023 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

from dataclasses import dataclass
from typing import List
from pathlib import Path
import sys

sys.path.append("docker")
from package.package_generator import output_dir as container_output_dir
from package.package_generator import common_parser as parser
from package.package_generator import make_ubuntu_parser
from package.packages import packages
import os
import json
import shlex
import subprocess


parser.add_argument(
    "--output-dir",
    help="provide a directory to place the built packages in",
    default=f"{os.path.join(os.getcwd(), 'out')}",
    type=os.path.abspath,
)
parser.add_argument(
    "--build-sapling-package",
    help="whether to build the sapling-params package",
    action="store_true",
)
parser.set_defaults(build_sapling_package=False)


def check_call(cmd):
    return subprocess.check_call(shlex.split(cmd))


def call(cmd):
    return subprocess.call(shlex.split(cmd))


def get_proc_output(cmd):
    return subprocess.run(shlex.split(cmd), capture_output=True, text=True)


def get_packages_to_build(arg):
    if arg:
        for pkg in arg:
            if not packages.get(pkg, None):
                raise Exception("Unknown package name.")
        return {key: packages[key] for key in arg}
    return packages


def validate_dists(dists, versions, target_os):
    for dist in dists:
        if dist not in versions:
            raise Exception(f"Distribution {dist} is not supported for {target_os}.")


@dataclass
class Arguments:
    os: str
    image: str
    cmd_args: str
    octez_version: str
    output_dir: Path
    distributions: List[str]
    docker_volumes: List[str]
    virtualisation_engine: str
    container_create_args: str


def run_build(args: Arguments) -> List[str]:

    virtualisation_engine = args.virtualisation_engine

    image = args.image

    target_os = args.os

    octez_version = args.octez_version

    # prebuild docker image before using containers
    check_call(
        f"""
    {virtualisation_engine}
    build -t tezos-{target_os}-{image}
    -f docker/package/Dockerfile-{target_os} --build-arg OCTEZ_VERSION={octez_version} --build-arg dist={image} .
    """
    )

    distros = args.distributions

    container_create_args = args.container_create_args

    cmd_args = args.cmd_args

    docker_volumes = args.docker_volumes

    container_id = get_proc_output(
        f"""
    {virtualisation_engine}
    create {" ".join(["-v " + v for v in docker_volumes])}
    {container_create_args}
    --env OCTEZ_VERSION={octez_version}
    --env OPAMSOLVERTIMEOUT=900
    -t tezos-{target_os}-{image} {cmd_args}
    """
    ).stdout.strip()

    exit_code = call(f"{virtualisation_engine} start -a {container_id}")

    os.makedirs(args.output_dir, exist_ok=True)

    call(
        f"""
    {virtualisation_engine} cp
    {container_id}:/tezos-packaging/docker/{container_output_dir}/. {args.output_dir}
    """
    )

    call(f"{virtualisation_engine} rm -v {container_id}")

    if exit_code:
        print("Unrecoverable error occured.")
        sys.exit(exit_code)

    with open(os.path.join(args.output_dir, ".artifact_list"), "r") as f:
        artifacts = f.read().splitlines()

    call(f"rm -rf {os.path.join(args.output_dir, '.artifact_list')}")

    return artifacts


def build_ubuntu(args=None) -> List[str]:
    if os.getenv("USE_PODMAN", None):
        virtualisation_engine = "podman"
    else:
        virtualisation_engine = "docker"

    if args is None:
        parser = make_ubuntu_parser(parser)
        args = parser.parse_args()

    docker_volumes = []

    if args.binaries_dir:
        binaries_dir_name = os.path.basename(args.binaries_dir)
        docker_volumes.append(
            f"{args.binaries_dir}:/tezos-packaging/docker/{binaries_dir_name}"
        )
    else:
        binaries_dir_name = None

    if args.sources_dir:
        sources_dir_name = os.path.basename(args.sources_dir)
        docker_volumes.append(
            f"{args.sources_dir}:/tezos-packaging/docker/{sources_dir_name}"
        )
    else:
        sources_dir_name = None

    target_os = args.os

    with open("./docker/supported_versions.json") as f:
        ubuntu_versions = json.loads(f.read()).get("ubuntu")

    if args.distributions:
        distributions = args.distributions
        validate_dists(distributions, ubuntu_versions, target_os)
    else:
        distributions = ubuntu_versions

    octez_version = os.getenv("OCTEZ_VERSION", None)

    if not octez_version:
        raise Exception("Environment variable OCTEZ_VERSION is not set.")

    if args.sources_dir and args.launchpad_sources:
        raise Exception(
            "--sources-dir and --launchpad-sources options are mutually exclusive."
        )

    # for ubuntu builds, since we lack `pbuilder` for now,
    # packages should be built in respective containers for better reproducibility
    images = distributions

    packages_to_build = get_packages_to_build(args.packages)

    if not args.build_sapling_package:
        packages_to_build.pop("tezos-sapling-params", None)

    output_dir = args.output_dir

    artifacts = []

    for image in images:

        distros = [image]

        artifacts += run_build(
            Arguments(
                os=target_os,
                image=image,
                octez_version=octez_version,
                output_dir=output_dir,
                distributions=distros,
                docker_volumes=docker_volumes,
                virtualisation_engine=virtualisation_engine,
                container_create_args="",
                cmd_args=" ".join(
                    [
                        f"--os {target_os}",
                        f"--binaries-dir {binaries_dir_name}"
                        if binaries_dir_name
                        else "",
                        f"--sources-dir {sources_dir_name}" if sources_dir_name else "",
                        f"--type {args.type}",
                        f"--distributions {' '.join(distros)}",
                        f"--launchpad-sources" if args.launchpad_sources else "",
                        f"--packages {' '.join(packages_to_build.keys())}",
                    ]
                ),
            )
        )

        # the same source archive has to be reused for an ubuntu package on different distros
        if sources_dir_name is None:
            sources_dir_name = "origs"
            docker_volumes.append(
                f"{args.output_dir}:/tezos-packaging/docker/{sources_dir_name}/"
            )

    return list(map(lambda x: os.path.join(args.output_dir, x), artifacts))


def build_fedora(args=None) -> List[str]:
    if os.getenv("USE_PODMAN", None):
        virtualisation_engine = "podman"
    else:
        virtualisation_engine = "docker"

    if args is None:
        args = parser.parse_args()

    docker_volumes = []

    if args.binaries_dir:
        binaries_dir_name = os.path.basename(args.binaries_dir)
        docker_volumes.append(
            f"{args.binaries_dir}:/tezos-packaging/docker/{binaries_dir_name}"
        )
    else:
        binaries_dir_name = None

    target_os = args.os

    with open("./docker/supported_versions.json") as f:
        fedora_versions = json.loads(f.read()).get("fedora")

    if args.distributions:
        distributions = args.distributions
        validate_dists(distributions, fedora_versions, target_os)
    else:
        distributions = ["native"]

    octez_version = os.getenv("OCTEZ_VERSION", None)

    if not octez_version:
        raise Exception("Environment variable OCTEZ_VERSION is not set.")

    # copr build infrastructure uses latest stable fedora and `mock` for builds
    # so we should also keep that way
    images = ["37"]

    packages_to_build = get_packages_to_build(args.packages)

    if not args.build_sapling_package:
        packages_to_build.pop("tezos-sapling-params", None)

    output_dir = args.output_dir

    artifacts = []

    for image in images:

        distros = distributions

        artifacts += run_build(
            Arguments(
                os=target_os,
                image=image,
                octez_version=octez_version,
                output_dir=output_dir,
                distributions=distros,
                docker_volumes=docker_volumes,
                virtualisation_engine=virtualisation_engine,
                container_create_args="",
                cmd_args=" ".join(
                    [
                        f"--os {target_os}",
                        f"--binaries-dir {binaries_dir_name}"
                        if binaries_dir_name
                        else "",
                        f"--type {args.type}",
                        f"--distributions {' '.join(distros)}",
                        f"--packages {' '.join(packages_to_build.keys())}",
                    ]
                ),
            )
        )

    return list(map(lambda x: os.path.join(args.output_dir, x), artifacts))


def main(args=None) -> List[str]:

    if args is None:
        args, _ = parser.parse_known_args()

    if args.os == "ubuntu":
        args = make_ubuntu_parser(parser).parse_args()
        artifacts = build_ubuntu(args)
    elif args.os == "fedora":
        args = parser.parse_args()
        artifacts = build_fedora(args)

    return artifacts


if __name__ == "__main__":
    main()
