#!/usr/bin/env bash

# SPDX-FileCopyrightText: 2023 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

set -euo pipefail

for version in $(jq -r '.ubuntu[]' docker/supported_versions.json); do
    docker build --build-arg dist="$version" --build-arg repo="tezos" -t ubuntu-test -f docker/tests/Dockerfile-ubuntu-test .
    docker run -rm ubuntu-test
    docker build --build-arg dist="$version" --build-arg repo="tezos-rc" -t ubuntu-test -f docker/tests/Dockerfile-ubuntu-test .
    docker run -rm ubuntu-test
done
