#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2023 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

import subprocess
import os
import re
import shutil
import json
import time

with open("meta.json") as f:
    octez_version = json.loads(f.read()).get("tezos_ref", "octez-v21.0")

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
