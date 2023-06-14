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

sys.path.append("docker/build")
from util.sign import *


def sign_ubuntu(args: Arguments):

    artifacts = get_artifact_list(args)

    identity = args.identity

    gpg = shutil.which("gpg")

    for f in artifacts:
        if f.endswith(".changes"):
            subprocess.check_call(
                f"sed -i 's/^Changed-By: .*$/Changed-By: {identity}/' {f}", shell=True
            )
            subprocess.check_call(f"debsign {f}", shell=True)


def main(args: Optional[Arguments] = None):

    parser.set_defaults(os="ubuntu")

    if args is None:
        args = fill_args(parser.parse_args())

    sign_ubuntu(args)


if __name__ == "__main__":
    main()
