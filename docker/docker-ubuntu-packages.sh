#! /usr/bin/env bash

# SPDX-FileCopyrightText: 2020 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: MPL-2.0

# This script builds native binary or source ubuntu packages with tezos
# binaries. To defined which packages to build you should pass
# 'binary' or 'source' as an argument to this script.
set -euo pipefail

docker build -t tezos-ubuntu -f docker/package/Dockerfile .
set +e
docker run -t --name package_builder tezos-ubuntu "$@"
docker cp package_builder:/tezos-packaging/docker/out .
set -e
docker rm -v package_builder
