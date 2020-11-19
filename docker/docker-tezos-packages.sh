#! /usr/bin/env bash

# SPDX-FileCopyrightText: 2020 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ

# This script builds native binary or source ubuntu or fedora packages
# with tezos binaries. Target OS is defined in the first passed argument.
# Package type can be defined in the second argument, 'source' and 'binary'
# types are supported.
set -euo pipefail

if [[ "${USE_PODMAN-}" == "True" ]]; then
    virtualisation_engine="podman"
else
    virtualisation_engine="docker"
fi

args=()

while true;
do
    arg="${1-}"
    if [[ -z "$arg" ]];
    then
        break
    fi
    case $arg in
        --os )
            target_os="$2"
            shift 2
            ;;
        * )
            args+=("$arg")
            shift
    esac
done

"$virtualisation_engine" build -t tezos-"$target_os" -f docker/package/Dockerfile-"$target_os" .
set +e
container_id="$("$virtualisation_engine" create --env TEZOS_VERSION="$TEZOS_VERSION" --env OPAMSOLVERTIMEOUT=120 -t tezos-"$target_os" "${args[@]}")"
"$virtualisation_engine" start -a "$container_id"
exit_code="$?"
"$virtualisation_engine" cp "$container_id":/tezos-packaging/docker/out .
set -e
"$virtualisation_engine" rm -v "$container_id"
exit "$exit_code"
