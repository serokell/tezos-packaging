#! /usr/bin/env bash

# SPDX-FileCopyrightText: 2023 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

set -euo pipefail

source "$HOME/.cargo/env"
opam init --bare --disable-sandboxing
make build-deps
