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

# FIXME dirty hack to make dune copy vendor directory to the build directory
with open("dune", "r") as f:
    dune = f.read()

with open("dune", "w") as f:
    f.write(dune.replace("(source_tree .cargo)", "(source_tree .cargo) (source_tree vendor)"))
