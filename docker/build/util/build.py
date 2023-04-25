# SPDX-FileCopyrightText: 2023 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

import os
import sys
import json
import copy
import shlex
import subprocess
from dataclasses import dataclass
from typing import List
from pathlib import Path

sys.path.append("docker")
from package.package_generator import output_dir as container_output_dir
from package.package_generator import common_parser
from package.package_generator import make_ubuntu_parser
from package.packages import packages


parser = copy.deepcopy(common_parser)
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
