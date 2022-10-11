#! /usr/bin/env bash

# SPDX-FileCopyrightText: 2021 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

# This script builds static tezos binaries. It expects patches required for static building to be
# in parent directory, it also accepts tezos version as an argument.
set -euo pipefail

tezos_version="$1"
git clone --single-branch --branch "$tezos_version" https://gitlab.com/tezos/tezos.git --depth 1
cd tezos

source "$HOME/.cargo/env"
export OPAMYES="true"
# Disable usage of instructions from the ADX extension to avoid incompatibility
# with old CPUs, see https://gitlab.com/dannywillems/ocaml-bls12-381/-/merge_requests/135/
export BLST_PORTABLE="yes"
opam init --bare --disable-sandboxing
make build-deps

# TODO remove on next upstream release
# see https://gitlab.com/tezos/tezos/-/issues/4005#note_1134995654
eval "$(opam env)"
opam install ledgerwallet-tezos --criteria=-changed

eval "$(opam env)" && PROFILE="static" make build
chmod +w octez-*
