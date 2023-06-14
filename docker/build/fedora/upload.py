#! /usr/bin/env python3
# SPDX-FileCopyrightText: 2023 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

import os
import re
import sys
import json
import subprocess
import argparse
from dataclasses import dataclass
from typing import List, Optional

sys.path.append("docker/build")
from util.upload import *


def upload_fedora(args: Arguments):

    with open("./docker/supported_versions.json") as f:
        fedora_versions = json.loads(f.read()).get("fedora")

    octez_version = os.getenv("OCTEZ_VERSION", None)

    if args.test:
        copr_project = "@Serokell/Tezos-test"
    elif re.search("v.*-rc[0-9]*", octez_version):
        copr_project = "@Serokell/Tezos-rc"
    else:
        copr_project = "@Serokell/Tezos"

    source_packages_path = args.directory

    if args.artifacts:
        packages = args.artifacts
    else:
        packages = list(
            map(
                lambda x: os.path.join(source_packages_path, x),
                os.listdir(source_packages_path),
            )
        )

    destination = args.destination

    if destination == "epel":
        chroots = ["epel-7-x86_64"]
    else:
        archs = ["x86_64", "aarch64"]
        chroots = [
            f"fedora-{version}-{arch}" for version in fedora_versions for arch in archs
        ]

    chroots = " ".join(f"-r {chroot}" for chroot in chroots)

    for f in filter(lambda x: x.endswith(".src.rpm"), packages):
        subprocess.check_call(
            f"copr-cli build {chroots} --nowait {copr_project} {f}",
            shell=True,
        )


def main(args: Optional[Arguments] = None):

    parser.set_defaults(os="fedora")

    if args is None:
        args = fill_args(parser.parse_args())

    upload_fedora(args)


if __name__ == "__main__":
    main()
