#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2023 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

import os
import sys
import shutil
import argparse
import subprocess
from dataclasses import dataclass
from typing import Optional, List

parser = argparse.ArgumentParser()
parser.add_argument(
    "--directory",
    "-d",
    help="provide a directory with packages to sign",
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
    help="provide a list of files' basenames to sign",
    nargs="+",
    default=[],
    required=False,
)
parser.add_argument(
    "--identity",
    "-i",
    help="provide an identity to sign packages",
    type=str,
    required=True,
)


@dataclass
class Arguments:
    os: str
    directory: str
    artifacts: List[str]
    identity: str


def fill_args(args) -> Arguments:
    return Arguments(
        os=args.os,
        directory=args.directory,
        artifacts=args.artifacts,
        identity=args.identity,
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


def sign_ubuntu(args: Arguments):

    artifacts = get_artifact_list(args)

    identity = args.identity

    gpg = shutil.which("gpg")

    for f in artifacts:
        if f.endswith(".changes"):
            subprocess.call(
                f"sed -i 's/^Changed-By: .*$/Changed-By: {identity}/' {f}", shell=True
            )
            subprocess.call(f"debsign {f}", shell=True)


def sign_fedora(args: Arguments):

    artifacts = get_artifact_list(args)

    identity = args.identity

    gpg = shutil.which("gpg")

    for f in artifacts:
        if f.endswith(".src.rpm"):
            subprocess.call(
                f'rpmsign --define="%_gpg_name {identity}" --define="%__gpg {gpg}" --addsign {f}',
                shell=True,
            )


def main(args: Optional[Arguments] = None):

    if args is None:
        args = fill_args(parser.parse_args())

    targets = ["ubuntu", "fedora"] if args.os is None else [args.os]

    for target in targets:
        if target == "ubuntu":
            sign_ubuntu(args)
        elif target == "fedora":
            sign_fedora(args)
        else:
            print(f"{target} target is not supported")


if __name__ == "__main__":
    main()
