#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2022 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

import argparse
import json
from subprocess import call

with open("flake.lock") as f:
    lock = json.load(f)

parser = argparse.ArgumentParser()
parser.add_argument("input", type=str)
parser.add_argument("rev", type=str)

args = parser.parse_args()

name = args.input

root = lock["root"]

nodes = lock["nodes"]

inputs = nodes[root]["inputs"]

lock_name = inputs[name]

meta = nodes[lock_name]["locked"]

url = f'{meta["type"]}:{meta["owner"]}/{meta["repo"]}/{args.rev}'

call(["nix", "flake", "lock", "--override-input", name, url])
