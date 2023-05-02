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

sys.path.append("docker")
from package.util.upload_common import *
from package.util.upload_ubuntu import upload_ubuntu
from package.util.upload_fedora import upload_fedora


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
