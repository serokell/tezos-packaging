#!/usr/bin/env bash

# SPDX-FileCopyrightText: 2023 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

set -euo pipefail

for version in $(jq -r '.fedora[]' docker/supported_versions.json); do
    docker build --build-arg dist="$version" --build-arg repo="Tezos" -t fedora-test -f docker/tests/Dockerfile-fedora-test .
    docker run --rm fedora-test
    docker build --build-arg dist="$version" --build-arg repo="Tezos-rc" -t fedora-test -f docker/tests/Dockerfile-fedora-test .
    docker run --rm fedora-test
done
