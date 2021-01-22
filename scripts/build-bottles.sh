#! /usr/bin/env bash
# SPDX-FileCopyrightText: 2021 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ

for formula in ./Formula/*.rb; do
    if [[ $formula != "*/tezos.rb" ]]; then
        brew install --build-bottle "$formula"
        brew bottle --force-core-tap "$formula"
        brew uninstall "$formula"
    fi
done
# https://github.com/Homebrew/brew/pull/4612#commitcomment-29995084
for bottle in ./*.bottle.*; do
    mv "$bottle" "${bottle/--/-}"
done
