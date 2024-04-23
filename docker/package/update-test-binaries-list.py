#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2023 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

import os
import json
from .packages import packages as all_packages
from .meta import packages_meta

binaries_json_path_suffix = "tests/binaries.json"


def update_binaries(binaries, field):
    binaries_json_path = os.path.join(os.environ["PWD"], binaries_json_path_suffix)
    with open(binaries_json_path, "r") as file:
        data = json.load(file)

    data[field] = binaries
    with open(binaries_json_path, "w") as file:
        json.dump(data, file, indent=4)
        file.write("\n")


def main():
    tag = packages_meta.tag
    binaries = []
    with open(f"{os.path.dirname(__file__)}/../octez-executables", "r") as f:
        binaries = [l.strip().replace("octez", "tezos") for l in f.readlines()]
    if not binaries:
        raise Exception(
            "Exception, while reading binaries list: binaries list is empty"
        )
    binaries.extend(["tezos-sapling-params", "tezos-baking"])

    field = "candidates" if "rc" in tag else "released"

    update_binaries(binaries, field)


if __name__ == "__main__":
    main()
