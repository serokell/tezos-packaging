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
# NOTE: it's important to keep the `tezos/.git` directory here, because the
# git tag is used to set the version in the Octez binaries.

subprocess.run(
    [
        "git",
        "clone",
        "https://github.com/ocaml/opam-repository.git",
        "opam-repository",
    ]
)

opam_repository_tag = (
    subprocess.run(
        ". ./tezos/scripts/version.sh; echo $opam_repository_tag",
        stdout=subprocess.PIPE,
        shell=True,
    )
    .stdout.decode()
    .strip()
)

os.chdir("opam-repository")
subprocess.run(["git", "checkout", opam_repository_tag])
subprocess.run(["rm", "-rf", ".git"])
subprocess.run(["opam", "admin", "cache"])
