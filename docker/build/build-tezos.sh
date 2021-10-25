#! /usr/bin/env bash

# SPDX-FileCopyrightText: 2020 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ

# This script builds static tezos binaries. It expects patches required for static building to be
# in parent directory, it also accepts tezos version as an argument.
set -euo pipefail

tezos_version="$1"
git clone --single-branch --branch "$tezos_version" https://gitlab.com/tezos/tezos.git --depth 1
cd tezos

git apply ../static.patch
export OPAMYES="true"
# Alpine 3.12 already provides rust with required version
# Uncomment and adjust when another version is required by Tezos
# wget https://sh.rustup.rs/rustup-init.sh
# chmod +x rustup-init.sh
# ./rustup-init.sh --profile minimal --default-toolchain 1.52.1 -y
# source "$HOME/.cargo/env"

opam init --bare --disable-sandboxing
make build-deps
eval "$(opam env)" && PROFILE="static" make && make build-sandbox
chmod +w tezos-*
