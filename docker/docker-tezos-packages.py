#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2022 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

import os
import sys
import shlex
import shutil
import subprocess
from package.packages import packages
from package.package_generator import parser
from package.package_generator import output_dir as container_output_dir

sys.path.append("docker")
from supported_versions import ubuntu_versions, fedora_versions


def check_call(cmd):
    return subprocess.check_call(shlex.split(cmd))


def call(cmd):
    return subprocess.call(shlex.split(cmd))


def get_proc_output(cmd):
    if sys.version_info.major == 3 and sys.version_info.minor < 7:
        return subprocess.run(shlex.split(cmd), stdout=subprocess.PIPE)
    else:
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


if os.getenv("USE_PODMAN", None):
    virtualisation_engine = "podman"
else:
    virtualisation_engine = "docker"

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
parser.add_argument(
    "--gpg-sign",
    "-s",
    help="provide an identity to sign packages",
    type=str,
)

parser.set_defaults(build_sapling_package=False)
args = parser.parse_args()

docker_volumes = ""

if args.binaries_dir:
    binaries_dir_name = os.path.basename(args.binaries_dir)
    docker_volumes = (
        f"-v {args.binaries_dir}:/tezos-packaging/docker/{binaries_dir_name}"
    )
else:
    binaries_dir_name = None

if args.sources_dir:
    sources_dir_name = os.path.basename(args.sources_dir)
    docker_volumes += (
        f"-v {args.sources_dir}:/tezos-packaging/docker/{sources_dir_name}"
    )
else:
    sources_dir_name = None

target_os = args.os

if target_os == "ubuntu":
    if args.distributions:
        distributions = args.distributions
        validate_dists(distributions, ubuntu_versions, target_os)
    else:
        distributions = ubuntu_versions
elif target_os == "fedora":
    if args.distributions:
        distributions = args.distributions
        validate_dists(distributions, fedora_versions, target_os)
    else:
        distributions = ["native"]
else:
    raise Exception("Unsupported target os: " + target_os)

octez_version = os.getenv("OCTEZ_VERSION", None)

if not octez_version:
    raise Exception("Environment variable OCTEZ_VERSION is not set.")

# copr build infrastructure uses latest stable fedora and `mock` for builds
# so we should also keep that way
# for ubuntu builds, since we lack `pbuilder` for now,
# packages should be built in respective containers for better reproducibility
images = ["37"] if target_os == "fedora" else distributions

for dist in images:
    # prebuild docker image before using containers
    check_call(
        f"""
    {virtualisation_engine}
    build -t tezos-{target_os}-{dist}
    -f docker/package/Dockerfile-{target_os} --build-arg OCTEZ_VERSION={octez_version} --build-arg dist={dist} .
    """
    )

packages_to_build = get_packages_to_build(args.packages)

if not args.build_sapling_package:
    packages_to_build.pop("tezos-sapling-params", None)

for image in images:
    distros = [image] if target_os == "ubuntu" else distributions
    cmd_args = " ".join(
        [
            f"--os {target_os}",
            f"--binaries-dir {binaries_dir_name}" if binaries_dir_name else "",
            f"--sources-dir {sources_dir_name}" if sources_dir_name else "",
            f"--type {args.type}",
            f"--distributions {' '.join(distros)}",
            f"--packages {' '.join(packages_to_build.keys())}",
        ]
    )

    container_create_args = (
        "--cap-add SYS_ADMIN" if target_os == "fedora" and args.distributions else ""
    )

    container_id = get_proc_output(
        f"""
    {virtualisation_engine}
    create {docker_volumes}
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

    # the same source archive has to be reused for an ubuntu package on different distros
    if sources_dir_name is None and target_os == "ubuntu":
        sources_dir_name = "origs"
        docker_volumes += (
            f"-v {args.output_dir}:/tezos-packaging/docker/{sources_dir_name}/"
        )

artifacts = (os.path.join(args.output_dir, x) for x in os.listdir(args.output_dir))
if args.gpg_sign and args.type == "source":
    if target_os == "ubuntu":
        for f in artifacts:
            if f.endswith(".changes"):
                call(f"sed -i 's/^Changed-By: .*$/Changed-By: {args.gpg_sign}/' {f}")
                call(f"debsign {f}")
    elif target_os == "fedora":
        gpg = shutil.which("gpg")
        for f in artifacts:
            if f.endswith(".src.rpm"):
                call(
                    f'rpmsign --define="%_gpg_name {args.gpg_sign}" --define="%__gpg {gpg}" --addsign {f}'
                )
