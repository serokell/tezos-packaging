#!/usr/bin/env nix-shell
#!nix-shell .. -A devShells.x86_64-linux.autorelease -i bash
# shellcheck shell=bash
# SPDX-FileCopyrightText: 2021 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

# This script takes the Buildkite build message, usually the last commit's title.

set -euo pipefail

# Project name, inferred from repository name
project=$(basename "$(pwd)")

# The directory in which artifacts will be created
TEMPDIR=$(mktemp -d)
function finish {
  rm -rf "$TEMPDIR"
}
trap finish EXIT

assets_dir=$TEMPDIR/assets

# Build tezos-release
nix-build . -A release.x86_64-linux -o "$TEMPDIR"/"$project" \
          --arg docker-binaries ./binaries/docker --arg docker-arm-binaries ./arm-binaries/docker
mkdir -p "$assets_dir"
# Move archive with binaries and tezos license to assets
shopt -s extglob
cp -L "$TEMPDIR"/"$project"/!(*.md) "$assets_dir"
# Iterate over assets, calculate sha256sum and sign them in order
# to include this additional info to the release assets as well
for asset in "$assets_dir"/*; do
    sha256sum "$asset" | sed 's/ .*/ /' > "$asset.sha256"
    gpg --armor --detach-sign "$asset"
done

msg_regex="Merge pull request .* from serokell\/auto\/(v.*)-release"
rc_regex="^v[0-9]+\.[0-9]+-rc[0-9]+"

# We create a pre-release in any case except if we are merging a stable version release PR
mode_flag="--prerelease"

if [[ ${1-""} =~ $msg_regex ]]; then
    tag="${BASH_REMATCH[1]}-$(jq -r '.release' meta.json)"
    if [[ ! $tag =~ $rc_regex ]]; then
        mode_flag=""
    fi
else
    tag="auto-release"

    # Delete autorelease if it exists
    gh release delete auto-release --yes || true
fi

# Update the tag
git fetch # So that the script can be run from an arbitrary checkout
git tag -f "$tag"
git push origin "$tag" --force

# Create release
gh release create -F "$TEMPDIR"/"$project"/release-notes.md "$mode_flag" "$tag" --title "$tag"

# Upload assets
gh release upload "$tag" "$assets_dir"/*
