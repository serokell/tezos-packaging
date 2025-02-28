#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2024 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

set -eu

# will be set by version.sh
opam_repository_tag=''
ocaml_version=''
. tezos/scripts/version.sh

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

# copying virtual opam file which depends on everything octez need
mkdir -p opam-repository/packages/octez-deps/octez-deps.dev
cp tezos/opam/virtual/octez-deps.opam.locked opam-repository/packages/octez-deps/octez-deps.dev/opam
mkdir -p opam-repository/packages/stdcompat/stdcompat.19
cp tezos/opam/virtual/stdcompat.opam.locked opam-repository/packages/stdcompat/stdcompat.19/opam

# This package adds some constraints to the solution found by the opam solver.
dummy_pkg=octez-dummy
dummy_opam_dir="opam-repository/packages/${dummy_pkg}/${dummy_pkg}.dev"
dummy_opam="${dummy_opam_dir}/opam"
mkdir -p "${dummy_opam_dir}"
echo 'opam-version: "2.0"' > "$dummy_opam"
echo "depends: [ \"ocaml\" { = \"$ocaml_version\" } ]" >> "$dummy_opam"
echo 'conflicts:[' >> "$dummy_opam"
grep -r "^flags: *\[ *avoid-version *\]" -l opam-repository/packages |
  LC_COLLATE=C sort -u |
  while read -r f; do
    f=$(dirname "$f")
    f=$(basename "$f")
    p=$(echo "$f" | cut -d '.' -f '1')
    v=$(echo "$f" | cut -d '.' -f '2-')
    echo "\"$p\" {= \"$v\"}" >> $dummy_opam
  done
# FIXME: https://gitlab.com/tezos/tezos/-/issues/5832
# opam unintentionally picks up a windows dependency. We add a
# conflict here to work around it.
echo '"ocamlbuild" {= "0.14.2+win" }' >> $dummy_opam
echo ']' >> "$dummy_opam"

# opam solver requires arch variable to be set, otherwise it fails to resolve anything
# but vendored opam deps have to be same for both architectures
# so we filter them separately and then merge with rsync
cp -r opam-repository x86_64
mv opam-repository arm64

filter() {
 pushd "$1"
 OPAMSOLVERTIMEOUT=600 opam admin filter --yes --resolve \
   "octez-deps,ocaml,ocaml-base-compiler,odoc,ledgerwallet-tezos,caqti-driver-postgresql,$dummy_pkg" \
   --environment "os=linux,arch=$1,os-family=debian"
 rm -rf packages/"$dummy_pkg" packages/octez-deps
 popd
}

filter x86_64
filter arm64

rsync -av x86_64/ arm64/
rm -rf x86_64
mv arm64 opam-repository

cd opam-repository
opam admin add-hashes sha256 sha512
opam admin cache
cd ..
