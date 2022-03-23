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
formulae=("tezos-accuser-011-PtHangz2" "tezos-accuser-012-Psithaca" "tezos-admin-client" "tezos-baker-011-PtHangz2" "tezos-baker-012-Psithaca" "tezos-client" "tezos-codec" "tezos-endorser-011-PtHangz2" "tezos-node" "tezos-sandbox" "tezos-signer")

# tezos-sapling-params is used as a dependency for some of the formulas
# so we handle it separately.
# We don't build the bottle for it because it is never updated over time.
ymlappend "
 - label: Install tezos-sapling-params
   key: install-tsp
   agents:
     queue: \"arm64-darwin\"
   if: build.tag =~ /^v.*/
   commands:
   - brew install --formula ./Formula/tezos-sapling-params.rb"

n=0
for f in "${formulae[@]}"; do
  n=$((n+1))
  ymlappend "

 - label: Check if $f bottle for Big Sur arm64 is already built
   key: check-built-$n
   if: build.tag =~ /^v.*/
   soft_fail:
   - exit_status: 3 # We don't want the pipeline to fail if the bottle's already built
   commands:
   - nix-shell ./scripts/shell.nix
       --run './scripts/check-bottle-built.sh \"$f\" \"arm64_big_sur\"'

 - label: Build $f bottle for Big Sur arm64
   key: build-bottle-$n
   agents:
     queue: \"arm64-darwin\"
   if: build.tag =~ /^v.*/
   depends_on: \"check-built-$n\"
   command: |
     if [ \$\$(buildkite-agent step get \"outcome\" --step \"check-built-$n\") == "passed" ]; then
       ./scripts/build-one-bottle.sh \"$f\"
     fi
   artifact_paths:
     - '*.bottle.*'"
done

ymlappend "
 - label: Uninstall tezos-sapling-params
   key: uninstall-tsp
   depends_on:"

for ((i=1; i<=n; i++)); do
  ymlappend "   - build-bottle-$i"
done

ymlappend "   agents:
     queue: \"arm64-darwin\"
   if: build.tag =~ /^v.*/
   commands:
   - brew uninstall ./Formula/tezos-sapling-params.rb

   # Since using the tag that triggered the pipeline isn't very resilient, we use the version
   # from the tezos-client formula, which hopefully will stay the most up-to-date.
 - label: Add Big Sur arm64 bottle hashes to formulae
   depends_on:
   - \"uninstall-tsp\"
   if: build.tag =~ /^v.*/
   soft_fail: true # No artifacts to download if all the bottles are already built
   commands:
   - mkdir -p \"Big Sur arm64\"
   - buildkite-agent artifact download \"*bottle.tar.gz\" \"Big Sur arm64/\"
   - export FORMULA_TAG=\"\$(sed -n 's/^\s\+version \"\(.*\)\"/\1/p' ./Formula/tezos-client.rb)\"
   - nix-shell ./scripts/shell.nix
       --run './scripts/sync-bottle-hashes.sh \"\$FORMULA_TAG\" \"Big Sur arm64\"'

 - label: Attach bottles to the release
   depends_on:
   - \"uninstall-tsp\"
   if: build.tag =~ /^v.*/
   soft_fail: true # No artifacts to download if all the bottles are already built
   commands:
   - buildkite-agent artifact download \"*bottle.tar.gz\" .
   - export FORMULA_TAG=\"\$(sed -n 's/^\s\+version \"\(.*\)\"/\1/p' ./Formula/tezos-client.rb)\"
   - nix-shell ./scripts/shell.nix
       --run 'gh release upload \"\$FORMULA_TAG\" *.bottle.*'"
