#! /usr/bin/env bash
# SPDX-FileCopyrightText: 2021 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

# This script takes the new tag as its argument.
# Run it from the base directory (tezos-packaging).

if [[ -d ./Formula ]]
then
    tag="$1"
    version="$2"
    find ./Formula -type f \( -name 'tezos-*.rb' ! -name 'tezos-sapling-params.rb' \) \
        -exec sed -i "s/version \"v.*\"/version \"$version\"/g" {} \; \
        -exec sed -i "s/:tag => \".*\"/:tag => \"$tag\"/g" {} \; \
        -exec sed -i "/catalina/d" {} \; \
        -exec sed -i "/monterey/d" {} \; \
        -exec sed -i "/arm64_monterey/d" {} \; \
        -exec sed -i "/mojave/d" {} \;
else
    echo "Please run this script from the base directory (tezos-packaging)."
fi
