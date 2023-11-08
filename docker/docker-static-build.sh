#! /usr/bin/env bash

# SPDX-FileCopyrightText: 2021 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

# This script builds static tezos-binaries using custom alpine image.
# It expects docker or podman to be installed and configured.

set -euo pipefail

if [ -z ${OCTEZ_EXECUTABLES+x} ]; then

    binaries=("octez-admin-client" "octez-dac-client" "octez-dac-node" "octez-client" "octez-node" "octez-signer" "octez-codec" "octez-smart-rollup-wasm-debugger" "octez-smart-rollup-node")

    for proto in $(jq -r ".active | .[]" ../protocols.json); do
        binaries+=("octez-accuser-$proto" "octez-baker-$proto" "octez-smart-rollup-client-$proto")
    done

    OCTEZ_EXECUTABLES="$( IFS=$' '; echo "${binaries[*]}" )"
else
    IFS=' ' read -r -a binaries <<< "$OCTEZ_EXECUTABLES"
fi

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

"$virtualisation_engine" build -t alpine-tezos -f "$docker_file" --build-arg=OCTEZ_VERSION="$OCTEZ_VERSION" --build-arg=OCTEZ_EXECUTABLES="$OCTEZ_EXECUTABLES" .
container_id="$("$virtualisation_engine" create alpine-tezos)"
for b in "${binaries[@]}"; do
    "$virtualisation_engine" cp "$container_id:/tezos/$b" "$b"
done
printf "%s\n" "${binaries[@]}" > "/tmp/binaries.txt"
echo "${binaries[@]}"
echo "$(ls /tmp | grep binaries.txt)"
"$virtualisation_engine" rm -v "$container_id"
