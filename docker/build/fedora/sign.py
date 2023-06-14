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


def sign_fedora(args: Arguments):

    artifacts = get_artifact_list(args)

    identity = args.identity

    gpg = shutil.which("gpg")

    for f in artifacts:
        if f.endswith(".src.rpm"):
            subprocess.check_call(
                f'rpmsign --define="%_gpg_name {identity}" --define="%__gpg {gpg}" --addsign {f}',
                shell=True,
            )


def main(args: Optional[Arguments] = None):

    parser.set_defaults(os="fedora")

    if args is None:
        args = fill_args(parser.parse_args())

    sign_fedora(args)


if __name__ == "__main__":
    main()
