#!/usr/bin/env nix-shell
#!nix-shell -p gitAndTools.hub git -i bash
# SPDX-FileCopyrightText: 2019 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: MPL-2.0

# Project name, inferred from repository name
project=$(basename $(pwd))

# The directory in which artifacts will be created
TEMPDIR=`mktemp -d`

# Build release.nix
nix-build release.nix -o $TEMPDIR/$project --arg timestamp $(date +\"%Y%m%d%H%M\")

# Delete release
hub release delete auto-release

# Update the tag
git fetch # So that the script can be run from an arbitrary checkout
git tag -f auto-release
git push --force --tags

# Combine all assets
assets=""
for file in $TEMPDIR/$project/*; do
    assets+="-a $file "
done

# Create release
hub release create $assets -m "Automatic build on $(date -I)" --prerelease auto-release
