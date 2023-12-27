#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2023 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

import re
import os
import json
from subprocess import call

masked_executables = ["octez-proxy-server"]
masked_protocols = ["alpha"]


def update_formulae_list(octez_executables):
    formulae = list(map(lambda x: x.replace("octez", "tezos"), octez_executables))

    with open(".github/workflows/build-bottles.yml") as f:
        workflow = f.read()
    # not using pyyaml here because it takes too much effort to preserve
    # the original structure of file
    workflow = re.sub("formula:.*", f"formula: [{', '.join(formulae)}]", workflow)
    with open(".github/workflows/build-bottles.yml", "w") as f:
        f.write(workflow)

    with open("./scripts/build-all-bottles.sh") as f:
        script = f.read()
    # wrap with quotes
    formulae = [f'"{formula}"' for formula in formulae]
    script = re.sub("formulae=.*", f"formulae=({' '.join(formulae)})", script)
    with open("./scripts/build-all-bottles.sh", "w") as f:
        f.write(script)


def update_protocol_list(active_protos):
    with open("./protocols.json") as f:
        protocols_json = json.loads(f.read())

    os.chdir("scripts")

    # remove previously active protocols
    for proto in protocols_json["active"]:
        call(f"./proto allow {proto}", shell=True)

    for proto in active_protos:
        call(f"./proto activate {proto}", shell=True)

    os.chdir("..")


with open("docker/octez-executables") as f:
    octez_executables = list(
        filter(
            lambda exec: exec and exec not in masked_executables, f.read().split("\n")
        )
    )

with open("docker/active-protocols") as f:
    active_protocols = list(
        filter(
            lambda proto: proto and proto not in masked_protocols, f.read().split("\n")
        )
    )

update_protocol_list(active_protocols)
update_formulae_list(octez_executables)
