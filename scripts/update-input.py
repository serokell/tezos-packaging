#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2022 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

import argparse
import re
import json
from subprocess import call

with open("flake.lock") as f:
    lock = json.load(f)["nodes"]

parser = argparse.ArgumentParser()
parser.add_argument("input", type=str)
parser.add_argument("rev", type=str)

args = parser.parse_args()

name = args.input
meta = lock[name]["locked"]
url = f'{meta["type"]}:{meta["owner"]}/{meta["repo"]}/{args.rev}'

call(["nix", "flake", "lock", "--override-input", name, url])
