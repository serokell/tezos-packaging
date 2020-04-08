#!/usr/bin/env nix-shell
#!nix-shell -p "callPackage ./scripts/dput.nix { }" debian-devscripts -i bash

set -euo pipefail

# Project name, inferred from repository name
project=$(basename "$(pwd)")

# The directory in which artifacts will be created
TEMPDIR=$(mktemp -d)
function finish {
    rm -rf "$TEMPDIR"
}
trap finish EXIT

nix-build -A debSource -o source-packages \
  --arg builderInfo "\"Serokell <hi@serokell.io>\"" \
  --arg timestamp "$(date +\"%Y%m%d%H%M\")" --arg date "\"$(date -R)\""

cp source-packages/* "$TEMPDIR"
chmod 700 -R "$TEMPDIR"
debsign "$TEMPDIR"/*.changes
dput -c ppa:serokell/tezos "$TEMPDIR"/*.changes
