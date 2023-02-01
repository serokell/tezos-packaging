#!/usr/bin/env bash

# SPDX-FileCopyrightText: 2023 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

# This script builds upx. alpine:3.12 for aarch64 doesn't provide upx,
# so we should build it natively for consistensy.
set -euo pipefail

git clone --depth 1 --branch v4.0.1 https://github.com/upx/upx.git

cd upx
git submodule update --init
make

cd build/release
make install
