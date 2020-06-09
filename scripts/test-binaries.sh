#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2019 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: MPL-2.0

# This script takes the filepath to the directory with tezos-binaries
# and test that they act normal within some simple scenarios

set -euo pipefail

binaries="$1"

for f in "$binaries"/tezos-*; do
    echo "$f"
    "./$f" --help &> /dev/null
done

# Test that tezos-node run works for carthagenet
"./$binaries/tezos-node" config init --data-dir node-dir --network carthagenet
"./$binaries/tezos-node" identity generate 1 --data-dir node-dir
timeout --preserve-status 5 "./$binaries/tezos-node" run --data-dir node-dir --network carthagenet
rm -rf node-dir

# Test that tezos-node run works for mainnet
"./$binaries/tezos-node" config init --data-dir node-dir --network mainnet
"./$binaries/tezos-node" identity generate 1 --data-dir node-dir
timeout --preserve-status 5 "./$binaries/tezos-node" run --data-dir node-dir --network mainnet
rm -rf node-dir
