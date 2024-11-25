#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2024 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

import subprocess
import os

os.chdir("tezos/src/rust_deps")
subprocess.run(["cargo-1.78", "vendor"], check=True)

with open(".cargo/config.toml", "a") as f:
    f.write(
        """
[source.crates-io]
replace-with = "vendored-sources"

[source.vendored-sources]
directory = "vendor"
    """
    )

# FIXME dirty hack to make dune copy vendor directory to the build directory and disignore internal files
with open("dune", "r") as f:
    dune = f.read()

with open("dune", "w") as f:
    f.write(
        dune.replace(
            "(source_tree .cargo)", "(source_tree .cargo) (source_tree vendor)"
        )
        + """
(subdir vendor/futures-core/src/task (dirs :standard __internal))
(subdir vendor/winnow/src (dirs :standard _tutorial _topic))
(subdir vendor/clap/src (dirs :standard _cookbook _derive _tutorial))
(subdir vendor/clap/src/_derive (dirs :standard _tutorial))
(subdir vendor/clap-3.2.25/src (dirs :standard _cookbook _derive _tutorial))
"""
    )

with open("build.sh", "r") as f:
    build_sh = f.read()

with open("build.sh", "w") as f:
    f.write(build_sh.replace("cargo", "cargo-1.78"))
