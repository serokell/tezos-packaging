#! /usr/bin/env bash
# SPDX-FileCopyrightText: 2021 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

# This script takes a directory where the bottles are stored and release tag as its arguments.
# Run it from the base directory (tezos-packaging).

set -e

if [[ -d ./Formula ]]
then
    if [[ -d "$1" ]]
    then
        regex="(tezos-.*)-v.*\.(monterey|arm64_monterey)\.bottle\.tar\.gz"
        for bottle in "$1"/tezos-*.bottle.tar.gz; do
            if [[ $bottle =~ $regex ]]; then
                bottle_hash=$(sha256sum "$bottle" | cut -d " " -f 1)
                formula_name="${BASH_REMATCH[1]}"
                os="${BASH_REMATCH[2]}"
                formula_file="./Formula/$formula_name.rb"
                if [[ -f $formula_file ]]; then
                    formula_tag="$(sed -n "s/^\s\+version \"\(.*\)\"/\1/p" "$formula_file")"
                    line="\    sha256 cellar: :any, $os: \"$bottle_hash\""
                    # Update only when formula has the same version as provided current tag
                    if [[ "$formula_tag" == "$2" ]]; then
                        sed -i "/root_url.*/a $line" "$formula_file"
                    else
                        echo "Current tag is $2, while formula has $formula_tag version"
                    fi
                fi
            fi
        done
    else
        echo "The passed directory $1 does not exist."
    fi
else
    echo "Please run this script from the base directory (tezos-packaging)."
fi
