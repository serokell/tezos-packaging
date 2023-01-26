#! /usr/bin/env bash

# SPDX-FileCopyrightText: 2021 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

# This script builds static tezos-binaries using custom alpine image.
# It expects docker or podman to be installed and configured.

set -euo pipefail

QEMU_AARCH64_INTERPRETER="${QEMU_AARCH64_INTERPRETER:-$(which qemu-aarch64-static)}"
QEMU_AARCH64_INTERPRETER_PATH="${QEMU_AARCH64_INTERPRETER_PATH:-/usr/bin/qemu-aarch64-static}"

binaries=("octez-admin-client" "octez-client" "octez-node" "octez-signer" "octez-codec")

for proto in $(jq -r ".active | .[]" ../protocols.json); do
    binaries+=("octez-accuser-$proto" "octez-baker-$proto")
done

binaries+=("octez-tx-rollup-node-PtLimaPt" "octez-tx-rollup-client-PtLimaPt")
binaries+=("octez-smart-rollup-client-PtMumbai" "octez-smart-rollup-node-PtMumbai")

if [[ "${USE_PODMAN-}" == "True" ]]; then
    virtualisation_engine="podman"
else
    virtualisation_engine="docker"
fi

arch="host"

if [[ -n "${1-}" ]]; then
    arch="$1"
fi

if [[ $arch == "host" ]]; then
    docker_file=build/Dockerfile
    image_name="alpine-tezos"
elif [[ $arch == "aarch64" ]]; then
    docker_file=build/Dockerfile.aarch64
    image_name="alpine-tezos-aarch64"
else
    echo "Unsupported architecture: $arch"
    echo "Only 'host' and 'aarch64' are currently supported"
    exit 1
fi

if [[ $arch == "aarch64" && $(uname -m) != "x86_64" ]]; then
    echo "Compiling for aarch64 is supported only from aarch64 and x86_64"
fi

QEMU_AARCH64_BASENAME="$(basename "$QEMU_AARCH64_INTERPRETER")"

if [[ $arch == "aarch64" ]]; then
    echo "Copying QEMU interpreter"
    cp -L --no-preserve=mode "$QEMU_AARCH64_INTERPRETER" .
    chmod +x "$QEMU_AARCH64_BASENAME"
fi
"$virtualisation_engine" build -t "$image_name" -f "$docker_file" --build-arg OCTEZ_VERSION="$OCTEZ_VERSION" \
    --build-arg QEMU_INTERPRETER_BINARY="$QEMU_AARCH64_BASENAME" \
    --build-arg QEMU_INTERPRETER_PATH="$QEMU_AARCH64_INTERPRETER_PATH" \
    --network=host .
container_id="$("$virtualisation_engine" create alpine-tezos)"
for b in "${binaries[@]}"; do
    "$virtualisation_engine" cp "$container_id:/tezos/$b" "$b"
done
"$virtualisation_engine" rm -v "$container_id"
if [[ $arch == "aarch64" ]]; then
    rm "$(basename "$QEMU_AARCH64_BASENAME")"
fi
