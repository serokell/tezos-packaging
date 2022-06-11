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

docker_volumes=()

while true;
do
    arg="${1-}"
    if [[ -z "$arg" ]];
    then
        break
    fi
    case $arg in
        --os )
            args+=("$arg" "$2")
            target_os="$2"
            shift 2
            ;;
        --sources )
            source_archive="$2"
            source_archive_name="$(basename "$2")"
            args+=("$arg" "$source_archive_name")
            docker_volumes+=("-v" "$PWD/$source_archive:/tezos-packaging/docker/$source_archive_name")
            shift 2
            ;;
        --binaries-dir )
            binaries_dir="$2"
            binaries_dir_name="$(basename "$2")"
            args+=("$arg" "$binaries_dir_name")
            docker_volumes+=("-v" "$PWD/$binaries_dir:/tezos-packaging/docker/$binaries_dir_name")
            shift 2
            ;;
        * )
            args+=("$arg")
            shift
            ;;
    esac
done

"$virtualisation_engine" build -t tezos-"$target_os" -f docker/package/Dockerfile-"$target_os" .
set +e
container_id="$("$virtualisation_engine" create "${docker_volumes[@]}" --env TEZOS_VERSION="$TEZOS_VERSION" --env OPAMSOLVERTIMEOUT=900 -t tezos-"$target_os" "${args[@]}")"
"$virtualisation_engine" start -a "$container_id"
exit_code="$?"
"$virtualisation_engine" cp "$container_id":/tezos-packaging/docker/out .
set -e
"$virtualisation_engine" rm -v "$container_id"
exit "$exit_code"
