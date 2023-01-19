#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2023 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

import subprocess
import os
import re
import shutil

octez_version = os.getenv("OCTEZ_VERSION", None)

if not octez_version:
    raise Exception("Environment variable OCTEZ_VERSION is not set.")

subprocess.run(
    [
        "git",
        "clone",
        "--branch",
        octez_version,
        "https://gitlab.com/tezos/tezos.git",
        "--depth",
        "1",
    ]
)

shutil.rmtree(os.path.join("tezos", ".git"))

subprocess.run(["git", "clone", "https://gitlab.com/tezos/opam-repository.git"])

with open("tezos/scripts/version.sh", "r") as f:
    opam_repository_tag = re.search(
        "^export opam_repository_tag=([0-9a-z]*)", f.read(), flags=re.MULTILINE
    ).group(1)
    os.chdir("opam-repository")
    subprocess.run(["git", "checkout", opam_repository_tag])
    subprocess.run(["rm", "-rf", ".git"])
    subprocess.run(["rm", "-r", "zcash-params"])
    subprocess.run(["opam", "admin", "cache"])
