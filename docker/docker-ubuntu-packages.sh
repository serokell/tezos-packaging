#! /usr/bin/env bash

# SPDX-FileCopyrightText: 2020 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: MPL-2.0

# This script builds native binary or source ubuntu packages with tezos
# binaries. To defined which packages to build you should pass
# 'binary' or 'source' as an argument to this script.
set -euo pipefail

if [[ "${USE_PODMAN-}" == "True" ]]; then
    virtualisation_engine="podman"
else
    virtualisation_engine="docker"
fi

"$virtualisation_engine" build -t tezos-ubuntu -f docker/package/Dockerfile .
set +e
container_id="$("$virtualisation_engine" create --env TEZOS_VERSION="$TEZOS_VERSION" -t tezos-ubuntu "$@")"
"$virtualisation_engine" start -a "$container_id"
"$virtualisation_engine" cp "$container_id":/tezos-packaging/docker/out .
set -e
"$virtualisation_engine" rm -v "$container_id"
