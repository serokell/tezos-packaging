#! /usr/bin/env bash

# SPDX-FileCopyrightText: 2021 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

# This script builds static tezos binaries. It expects patches required for static building to be
# in parent directory.
set -euo pipefail

eval "$(opam env)" && PROFILE="static" make build
chmod +w octez-*
