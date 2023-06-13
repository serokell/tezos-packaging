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
    default=".",
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
