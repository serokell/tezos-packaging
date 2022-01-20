#! /usr/bin/env bash
# SPDX-FileCopyrightText: 2021 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ

# This script takes a directory where the bottles are stored as its argument.
# Run it from the base directory (tezos-packaging).

set -e

if [[ -d ./Formula ]]
then
    if [[ -d "$1" ]]
    then
        regex="(tezos-.*)-v.*\.(catalina|big_sur|arm64_big_sur)\.bottle\.tar\.gz"
        for bottle in "$1"/tezos-*.bottle.tar.gz; do
            if [[ $bottle =~ $regex ]]; then
                bottle_hash=$(sha256sum "$bottle" | cut -d " " -f 1)
                formula_name="${BASH_REMATCH[1]}"
                os="${BASH_REMATCH[2]}"

                if [[ -f "./Formula/$formula_name.rb" ]]; then
                    line="\    sha256 cellar: :any, $os: \"$bottle_hash\""
                    sed -i "/root_url.*/a $line" "./Formula/$formula_name.rb"
                fi
            fi
        done
    else
        echo "The passed directory $1 does not exist."
    fi
else
    echo "Please run this script from the base directory (tezos-packaging)."
fi
