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

parser = argparse.ArgumentParser()
parser.add_argument(
    "--directory",
    "-d",
    help="provide a directory with packages to upload",
    default=f"{os.path.join(os.getcwd(), '.')}",
    type=os.path.abspath,
)
parser.add_argument(
    "--os",
    help="provide an os the packages built for",
    type=str,
)
parser.add_argument(
    "--artifacts",
    "-p",
    help="provide a list of files to upload",
    nargs="+",
    default=[],
    required=False,
)
parser.add_argument(
    "--upload",
    help="upload packages to the specified repository",
    default=None,
    const="regular",
    nargs="?",
)
parser.add_argument(
    "--test",
    help="upload packages to the test repository",
    action="store_true",
)
parser.set_defaults(test=False)


@dataclass
class Arguments:
    os: str
    directory: str
    artifacts: List[str]
    destination: str
    test: bool


def fill_args(args) -> Arguments:
    return Arguments(
        os=args.os,
        directory=args.directory,
        artifacts=args.artifacts,
        destination=args.upload,
        test=args.test,
    )


def get_artifact_list(args: Arguments):

    artifacts = args.artifacts

    if not artifacts:
        artifacts = [
            os.path.join(args.directory, x) for x in os.listdir(args.directory)
        ]
    else:
        artifacts = [os.path.join(args.directory, x) for x in args.artifacts]

    filtered = []
    for x in artifacts:
        if not os.path.exists(x):
            print("Artifact does not exist: ", x)
        else:
            filtered.append(x)

    return filtered


def upload_ubuntu(args: Arguments):

    with open("dput.cfg", "w") as dput_cfg:
        dput_cfg.write(
            f"""
[DEFAULT]
login	 = *
method = ftp
hash = md5
allow_unsigned_uploads = 0
allow_dcut = 0
run_lintian = 0
run_dinstall = 0
check_version = 0
scp_compress = 0
post_upload_command	=
pre_upload_command =
passive_ftp = 1
default_host_main	=
allowed_distributions	= (?!UNRELEASED)

[tezos-serokell]
fqdn      = ppa.launchpad.net
method    = ftp
incoming  = ~serokell/ubuntu/tezos
login     = anonymous

[tezos-rc-serokell]
fqdn        = ppa.launchpad.net
method      = ftp
incoming    = ~serokell/ubuntu/tezos-rc
login       = anonymous

[tezos-test-serokell]
fqdn        = ppa.launchpad.net
method      = ftp
incoming    = ~serokell/ubuntu/tezos-test
login       = anonymous
    """
        )

    octez_version = os.getenv("OCTEZ_VERSION", None)

    if args.test:
        launchpad_ppa = "tezos-test-serokell"
    elif re.search("v.*-rc[0-9]*", octez_version):
        launchpad_ppa = "tezos-rc-serokell"
    else:
        launchpad_ppa = "tezos-serokell"

    source_packages_path = args.directory

    packages = get_artifact_list(args)

    for f in filter(lambda x: x.endswith(".changes"), packages):
        subprocess.call(
            f"execute-dput -c dput.cfg {launchpad_ppa} {os.path.join(source_packages_path, f)}",
            shell=True,
        )


def upload_fedora(args: Arguments):

    fedora_versions = json.loads("./docker/supported_versions.json").get("fedora")

    octez_version = os.getenv("OCTEZ_VERSION", None)

    if args.test:
        copr_project = "@Serokell/Tezos-test"
    elif re.search("v.*-rc[0-9]*", octez_version):
        copr_project = "@Serokell/Tezos-rc"
    else:
        copr_project = "@Serokell/Tezos-test"

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
        chroots = ["epel-x86_64"]
    else:
        archs = ["x86_64", "aarch64"]
        chroots = [
            f"fedora-{version}-{arch}" for version in fedora_versions for arch in archs
        ]

    chroots = " ".join(f"-r {chroot}" for chroot in chroots)

    for f in filter(lambda x: x.endswith(".src.rpm"), packages):
        subprocess.call(
            f"copr-cli build {chroots} --nowait {copr_project} {f}",
            shell=True,
        )


def main(args: Optional[Arguments] = None):
    if args is None:
        args = fill_args(parser.parse_args())

    targets = ["ubuntu", "fedora"] if args.os is None else [args.os]

    for target in targets:
        if target == "ubuntu":
            upload_ubuntu(args)
        elif target == "fedora":
            upload_fedora(args)
        else:
            print(f"{target} target is not supported")


if __name__ == "__main__":
    main()
