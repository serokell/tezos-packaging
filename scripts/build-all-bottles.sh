#! /usr/bin/env nix-shell
#! nix-shell .. -A autorelease-macos -i bash
# shellcheck shell=bash

# SPDX-FileCopyrightText: 2022 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

if [ -z "$1" ] ; then
    echo "Please call this script with the name of the OS for which to build the bottles."
    exit 1
fi

set -euo pipefail

# we don't bottle meta-formulas that contain only services
formulae=("tezos-accuser-013-PtJakart" "tezos-admin-client" "tezos-baker-013-PtJakart" "tezos-client" "tezos-codec" "tezos-node" "tezos-sandbox" "tezos-signer")

# tezos-sapling-params is used as a dependency for some of the formulas
# so we handle it separately.
# We don't build the bottle for it because it is never updated over time.
brew install --formula ./Formula/tezos-sapling-params.rb

for f in "${formulae[@]}"; do
  # check if the formula doesn't already have a bottle in its respective release
  if ./scripts/check-bottle-built.sh "$f" "$1"; then
    # build a bottle
    if ./scripts/build-one-bottle.sh "$f"; then
      # upload the bottle to its respective release
      FORMULA_TAG="$(sed -n "s/^\s\+version \"\(.*\)\"/\1/p" "./Formula/$f.rb")"
      gh release upload "$FORMULA_TAG" "$f"*.bottle.* ||
        >&2 echo "Bottle for $f couldn't be uploaded to $FORMULA_TAG release."
    else
      >&2 echo "Bottle for $f couldn't be built."
    fi
  fi
done

brew uninstall ./Formula/tezos-sapling-params.rb
# opam doesn't always handle the situation when the same library is present for
# multiple architectures, see https://github.com/ocaml/opam-repository/issues/20941
# so all dependencies are cleared after bottles builds to avoid errors
brew autoremove
