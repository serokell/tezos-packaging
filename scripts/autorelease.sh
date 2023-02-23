#!/usr/bin/env bash
# shellcheck shell=bash
# SPDX-FileCopyrightText: 2021 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

set -euo pipefail

# The directory in which artifacts will be created
TEMPDIR=$(mktemp -d)
function finish {
  rm -rf "$TEMPDIR"
}
trap finish EXIT

assets_dir=$TEMPDIR/assets

gh release download "v16.0-rc3-1" -D "$assets_dir" -p "*-arm64"

# Iterate over assets, calculate sha256sum and sign them in order
# to include this additional info to the release assets as well
for asset in "$assets_dir"/*; do
    sha256sum "$asset" | sed 's/ .*/ /' > "$asset.sha256"
    gpg --armor --detach-sign "$asset"
done

# Upload assets
gh release upload "v16.0-rc3-1" "$assets_dir"/* --clobber
