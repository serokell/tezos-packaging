#! /usr/bin/env bash
# SPDX-FileCopyrightText: 2021 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

# This script takes the new tag as its argument.
# Run it from the base directory (tezos-packaging).

if [[ -d ./Formula ]]
then
    regex="(v.*)-[0-9]*"
    if [[ $1 =~ $regex ]]; then
        tag="${BASH_REMATCH[0]}"
        version="${BASH_REMATCH[1]}"
        find ./Formula -type f \( -name 'tezos-*.rb' ! -name 'tezos-sapling-params.rb' \) \
            -exec sed -i "s/version \"v.*\"/version \"$tag\"/g" {} \; \
            -exec sed -i "s/:tag => \".*\"/:tag => \"$version\"/g" {} \; \
            -exec sed -i "/catalina/d" {} \; \
            -exec sed -i "/monterey/d" {} \; \
            -exec sed -i "/arm64_monterey/d" {} \; \
            -exec sed -i "/mojave/d" {} \;
    else
        echo "The argument does not look like a tag, which should have a form of 'v*-[0-9]*'"
    fi
else
    echo "Please run this script from the base directory (tezos-packaging)."
fi
