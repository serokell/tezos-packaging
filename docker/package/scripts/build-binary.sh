#!/usr/bin/env bash

# SPDX-FileCopyrightText: 2021 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA
set -euo pipefail

export OPAMYES=true
mkdir opamroot
export OPAMROOT=$PWD/opamroot

dune_filepath="$1"
binary_name="$2"

cd tezos
opam init local ../opam-repository --bare --disable-sandboxing
opam switch create . --repositories=local --no-install

eval "$(opam env)"
OPAMASSUMEDEPEXTS=true opam install conf-rust conf-rust-2021

export CFLAGS="-fPIC ${CFLAGS:-}"
opam install opam/virtual/octez-deps.opam --deps-only --criteria="-notuptodate,-changed,-removed"

eval "$(opam env)"
dune build "$dune_filepath"
cp "./_build/default/$dune_filepath" "../$binary_name"
cd ..
