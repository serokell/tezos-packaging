#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2023 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

import os
import sys
import json
import shlex
import subprocess
from dataclasses import dataclass
from typing import List
from pathlib import Path

sys.path.append("docker")
from package.package_generator import output_dir as container_output_dir
from package.package_generator import common_parser as parser
from package.package_generator import make_ubuntu_parser
from package.packages import packages

sys.path.append("docker/build")
from util.build import *


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
    images = ["41"]

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

    parser.set_defaults(os="fedora")

    if args is None:
        args = parser.parse_args()

    artifacts = build_fedora(args)

    return artifacts


if __name__ == "__main__":
    main()
