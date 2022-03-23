#! /usr/bin/env bash
# SPDX-FileCopyrightText: 2022 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

# This script takes the name of the binary for which to check if the bottle
# has already been built and the OS name as its arguments.

set -eo pipefail

if [ -z "$1" ] || [ -z "$2" ] ; then
    echo "Please call this script with the name of the formula and the OS name."
    exit 1
fi

if [ ! -f "./Formula/$1.rb" ] ; then
    echo "This formula doesn't exist."
    exit 2
fi

tag=$(sed -n "s/^\s\+version \"\(.*\)\"/\1/p" "./Formula/$1.rb")

gh release view "$tag" | grep "$1.*\.$2.bottle.tar.gz"

if [ $? -eq 0 ]; then
    echo "Bottle is already attached to the $tag release."
    exit 3
else
    exit 0
fi
