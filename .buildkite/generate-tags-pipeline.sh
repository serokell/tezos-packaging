#! /usr/bin/env nix-shell
#! nix-shell shell.nix -i bash

# SPDX-FileCopyrightText: 2022 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

# This script generates part of the .buildkite/pipeline-for-tags.yml config file
# by appending every step associated with bottle building to the steps defined there.

set -euo pipefail

ymlappend () {
    echo "$1" >> .buildkite/pipeline-for-tags.yml
}

# we don't bottle meta-formulas that contain only services
formulae=("tezos-accuser-012-Psithaca" "tezos-admin-client" "tezos-baker-012-Psithaca" "tezos-client" "tezos-codec" "tezos-node" "tezos-sandbox" "tezos-signer")
architecture=("arm64" "x86_64")
declare -A queues=(["arm64"]="arm64-darwin" ["x86_64"]="x86_64-rosetta-darwin")
declare -A brew_bottle_oses=(["arm64"]="arm64_big_sur" ["x86_64"]="big_sur")

for arch in "${architecture[@]}"; do
  # tezos-sapling-params is used as a dependency for some of the formulas
  # so we handle it separately.
  # We don't build the bottle for it because it is never updated over time.
  queue="${queues[$arch]}"
  brew_bottle_os=${brew_bottle_oses[$arch]}
  ymlappend "
 - label: Install tezos-sapling-params-$arch
   key: install-tsp-$arch
   agents:
     queue: \"$queue\"
   if: build.tag =~ /^v.*/
   commands:
   - brew install --formula ./Formula/tezos-sapling-params.rb"

  n=0
  for f in "${formulae[@]}"; do
    n=$((n+1))
    ymlappend "
 - label: Check if $f bottle for Big Sur $arch is already built
   key: check-built-$arch-$n
   if: build.tag =~ /^v.*/
   soft_fail:
   - exit_status: 3 # We don't want the pipeline to fail if the bottle's already built
   commands:
   - nix-shell ./scripts/shell.nix
       --run './scripts/check-bottle-built.sh \"$f\" \"$brew_bottle_os\"'

 - label: Build $f bottle for Big Sur $arch
   key: build-bottle-$arch-$n
   agents:
     queue: \"$queue\"
   if: build.tag =~ /^v.*/
   depends_on: \"check-built-$arch-$n\"
   command: |
     if [ \$\$(buildkite-agent step get \"outcome\" --step \"check-built-$arch-$n\") == "passed" ]; then
       ./scripts/build-one-bottle.sh \"$f\"
     fi
   artifact_paths:
     - '*.bottle.*'"
  done

  ymlappend "
 - label: Uninstall tezos-sapling-params $arch
   key: uninstall-tsp-$arch
   depends_on:"

  for ((i=1; i<=n; i++)); do
    ymlappend "   - build-bottle-$arch-$i"
  done

  ymlappend "   agents:
     queue: \"$queue\"
   if: build.tag =~ /^v.*/
   commands:
   - brew uninstall ./Formula/tezos-sapling-params.rb
   # opam doesn't always handle the situation when the same library is present for
   # multiple architectures, see https://github.com/ocaml/opam-repository/issues/20941
   # so all dependencies are cleared after bottles builds to avoid errors
   - brew autoremove

 # To avoid running two brew processes together
 - wait"

done

ymlappend "
 - label: Add Big Sur bottle hashes to formulae
   depends_on:"
for arch in "${architecture[@]}"; do
   ymlappend "   - \"uninstall-tsp-$arch\""
done
   ymlappend "   if: build.tag =~ /^v.*/
   soft_fail: true # No artifacts to download if all the bottles are already built
   commands:
   - mkdir -p \"Big Sur\"
   - buildkite-agent artifact download \"*bottle.tar.gz\" \"Big Sur/\"
   - export FORMULA_TAG=\"\$(sed -n 's/^\s\+version \"\(.*\)\"/\1/p' ./Formula/tezos-client.rb)\"
   - nix-shell ./scripts/shell.nix
       --run './scripts/sync-bottle-hashes.sh \"\$\$FORMULA_TAG\" \"Big Sur\"'
 - label: Attach bottles to the release
   depends_on:"
for arch in "${architecture[@]}"; do
   ymlappend "   - \"uninstall-tsp-$arch\""
done
   ymlappend "   if: build.tag =~ /^v.*/
   soft_fail: true # No artifacts to download if all the bottles are already built
   commands:
   - buildkite-agent artifact download \"*bottle.tar.gz\" .
   - export FORMULA_TAG=\"\$(sed -n 's/^\s\+version \"\(.*\)\"/\1/p' ./Formula/tezos-client.rb)\"
   - nix-shell ./scripts/shell.nix
       --run 'gh release upload \"\$\$FORMULA_TAG\" *.bottle.*'"
