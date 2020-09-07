#! /usr/bin/env bash

# SPDX-FileCopyrightText: 2020 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: MPL-2.0

# This script builds static tezos-binaries using custom alpine image.
# It expects docker to be installed and configured.

set -euo pipefail

binaries=("tezos-admin-client" "tezos-client" "tezos-node" "tezos-signer")

for proto in $(jq -r ".active | .[]" ../protocols.json); do
    binaries+=("tezos-accuser-$proto" "tezos-baker-$proto" "tezos-endorser-$proto")
done

arch="host"

if [[ -n "${1-}" ]]; then
    arch="$1"
fi

if [[ $arch == "host" ]]; then
    docker_file=build/Dockerfile
elif [[ $arch == "aarch64" ]]; then
    docker_file=build/Dockerfile.aarch64
else
    echo "Unsupported architecture: $arch"
    echo "Only 'host' and 'aarch64' are currently supported"
    exit 1
fi

if [[ $arch == "aarch64" && $(uname -m) != "x86_64" ]]; then
    echo "Compiling for aarch64 is supported only from aarch64 and x86_64"
fi

docker build -t alpine-tezos -f "$docker_file" --build-arg TEZOS_VERSION="$TEZOS_VERSION" .
container_id="$(docker create alpine-tezos)"
for b in "${binaries[@]}"; do
    docker cp "$container_id:/tezos/$b" "$b"
done
docker rm -v "$container_id"
