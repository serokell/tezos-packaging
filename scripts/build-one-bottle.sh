#! /usr/bin/env bash
# SPDX-FileCopyrightText: 2022 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

# Newer brew versions fail when checking for a rebuild version of non-core taps.
# So for now we skip the check with '--no-rebuild'

set -eo pipefail

if [ -z "$1" ] ; then
    echo "Please call this script with the name of the binary for which to build the bottle."
    exit 1
fi

brew install --formula --build-bottle "./Formula/$1.rb"
brew bottle --force-core-tap --no-rebuild "./Formula/$1.rb"
brew uninstall --formula "./Formula/$1.rb"
# https://github.com/Homebrew/brew/pull/4612#commitcomment-29995084
mv "$1"*.bottle.* "$(echo $1*.bottle.* | sed s/--/-/)"
