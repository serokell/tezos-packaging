#! /usr/bin/env bash

# SPDX-FileCopyrightText: 2021 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

# This script builds static tezos binaries. It expects patches required for static building to be
# in parent directory.
set -euo pipefail

eval "$(opam env)"
# Disable usage of instructions from the ADX extension to avoid incompatibility
# with old CPUs, see https://gitlab.com/dannywillems/ocaml-bls12-381/-/merge_requests/135/
export BLST_PORTABLE="yes"
make static
chmod +w octez-*
