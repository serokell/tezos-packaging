#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2023 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

from dataclasses import dataclass
from typing import List
from pathlib import Path
import sys

sys.path.append("docker")
from package.package_generator import output_dir as container_output_dir
from package.package_generator import common_parser as parser
from package.package_generator import make_ubuntu_parser
from package.packages import packages
from package.util.build_common import *
from package.util.build_ubuntu import build_ubuntu
from package.util.build_fedora import build_fedora
import os
import json
import shlex
import subprocess


def main(args=None) -> List[str]:

    if args is None:
        args, _ = parser.parse_known_args()

    if args.os == "ubuntu":
        args = make_ubuntu_parser(parser).parse_args()
        artifacts = build_ubuntu(args)
    elif args.os == "fedora":
        args = parser.parse_args()
        artifacts = build_fedora(args)

    return artifacts


if __name__ == "__main__":
    main()
