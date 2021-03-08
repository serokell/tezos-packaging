#! /usr/bin/env bash

# SPDX-FileCopyrightText: 2020 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ

# This script builds static tezos binaries. It expects patches required for static building to be
# in parent directory, it also accepts tezos version as an argument.
set -euo pipefail

tezos_version="$1"
git clone --single-branch --branch "$tezos_version" https://gitlab.com/tezos/tezos.git --depth 1
cd tezos

git apply ../static.patch
export OPAMYES="true"
eval "$(opam env)" && make && make build-sandbox
