#! /usr/bin/env bash

# SPDX-FileCopyrightText: 2020 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: MPL-2.0

# This script builds static tezos-binaries using custom alpine image.
# It expects docker to be installed and configured.

set -euo pipefail

binaries=("tezos-accuser-006-PsCARTHA" "tezos-admin-client" "tezos-baker-006-PsCARTHA"
          "tezos-client" "tezos-endorser-006-PsCARTHA" "tezos-node" "tezos-signer"
         )

echo $TEZOS_VERSION
docker build -t alpine-tezos -f build/Dockerfile --build-arg TEZOS_VERSION="$TEZOS_VERSION" .
container_id="$(docker create alpine-tezos)"
for b in "${binaries[@]}"; do
    docker cp "$container_id:/tezos/$b" "$b"
done
docker rm -v "$container_id"
