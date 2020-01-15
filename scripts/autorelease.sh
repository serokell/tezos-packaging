#!/usr/bin/env nix-shell
#!nix-shell -p gitAndTools.hub git rename -i bash
# SPDX-FileCopyrightText: 2019 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: MPL-2.0

# Project name, inferred from repository name
project=$(basename $(pwd))

# The directory in which artifacts will be created
TEMPDIR=`mktemp -d`
assets_dir=$TEMPDIR/assets

# Build release.nix
nix-build release.nix -o $TEMPDIR/$project --arg timestamp $(date +\"%Y%m%d%H%M\")
mkdir -p $assets_dir
# Create archives with deb and rpm packages
tar -cvzf $assets_dir/packages-deb.tar.gz --mode='u+rwX' -C $TEMPDIR/$project $(cd $TEMPDIR/$project && ls *.deb)
tar -cvzf $assets_dir/packages-rpm.tar.gz --mode='u+rwX' -C $TEMPDIR/$project $(cd $TEMPDIR/$project && ls *.rpm)
# Move these archives to assets
cp $TEMPDIR/$project/*.tar.gz $assets_dir
cp $TEMPDIR/$project/LICENSE $assets_dir
# Unpack binaries
mkdir -p $assets_dir/binaries-babylonnet $assets_dir/binaries-mainnet
tar -C $assets_dir/binaries-mainnet -xvzf $TEMPDIR/$project/binaries-mainnet-*.tar.gz
tar -C $assets_dir/binaries-babylonnet -xvzf $TEMPDIR/$project/binaries-babylonnet-*.tar.gz
# Add corresponding babylonnet or mainnet suffixes
rename 's/(.*)$/$1-babylonnet/' $assets_dir/binaries-babylonnet/*
rename 's/(.*)$/$1-mainnet/' $assets_dir/binaries-mainnet/*
# Move renamed binaries to assets
mv $assets_dir/binaries-*/* $assets_dir/
rm -r $assets_dir/*/

# Delete release
hub release delete auto-release

# Update the tag
git fetch # So that the script can be run from an arbitrary checkout
git tag -f auto-release
git push --force --tags

# Combine all assets
assets=""
for file in $assets_dir/*; do
    assets+="-a $file "
done

# Create release
hub release create $assets -m "Automatic build on $(date -I)" --prerelease auto-release
