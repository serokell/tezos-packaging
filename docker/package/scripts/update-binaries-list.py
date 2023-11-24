# SPDX-FileCopyrightText: 2023 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

import os
import sys
import json

binaries_json_path_suffix = "tests/binaries.json"
binaries_list_path_suffix = "tmp/binaries.txt"


def update_binaries(binaries, field):
    binaries_json_path = os.path.join(os.environ["PWD"], binaries_json_path_suffix)
    with open(binaries_json_path, "r") as file:
        data = json.load(file)

    data[field] = binaries
    with open(binaries_json_path, "w") as file:
        json.dump(data, file, indent=4)
        file.write("\n")


def main():
    tag = os.environ["BUILDKITE_TAG"]
    binaries = []

    binaries_list_path = os.path.join(os.environ["PWD"], binaries_list_path_suffix)
    with open(binaries_list_path, "r") as f:
        binaries = [l.strip().replace("octez", "tezos") for l in f.readlines()]

    binaries += ["tezos-baking", "tezos-sampling-params"]

    if not binaries:
        raise Exception(
            "Exception, while reading binaries list: binaries list is empty"
        )

    field = "candidates" if "rc" in tag else "released"

    update_binaries(binaries, field)
    os.remove(binaries_list_path)


if __name__ == "__main__":
    main()
