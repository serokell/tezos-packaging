#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2024 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

set -eu

opam_repository_tag=''
ocaml_version=''
source tezos/scripts/version.sh

echo "Shallow clone of opam repository (requires git protocol version 2)"
mkdir opam-repository
cd opam-repository
git init
git config --local protocol.version 2
git remote add origin https://github.com/ocaml/opam-repository
git fetch --depth 1 origin "$opam_repository_tag"
git checkout "$opam_repository_tag"
# No need to store the whole Git history in the Docker images.
rm -rf .git .github .gitignore .gitattributes
cd ..

echo "Add package: octez-deps"
mkdir -p opam-repository/packages/octez-deps/octez-deps.dev
cp tezos/opam/virtual/octez-deps.opam.locked opam-repository/packages/octez-deps/octez-deps.dev/opam

cd opam-repository
OPAMSOLVERTIMEOUT=600 opam admin filter --yes --resolve octez-deps
rm -rf packages/octez-deps
opam admin cache
cd ..
