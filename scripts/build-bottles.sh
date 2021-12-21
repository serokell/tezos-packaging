#! /usr/bin/env bash
# SPDX-FileCopyrightText: 2021 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ

# Newer brew versions fail when checking for a rebuild version of non-core taps.
# So for now we skip the check with '--no-rebuild'
build_bottle () {
    brew install --formula --build-bottle "$1"
    brew bottle --force-core-tap --no-rebuild "$1"
    brew uninstall "$1"
}

# tezos-sapling-params is used as a dependency for some of the formulas
# so we handle it separately.
# We don't build the bottle for it because it is never updated over time.
brew install --formula ./Formula/tezos-sapling-params.rb

# we don't bottle meta-formulas that contains only services
build_bottle ./Formula/tezos-accuser-011-PtHangz2.rb
build_bottle ./Formula/tezos-accuser-012-PsiThaCa.rb
build_bottle ./Formula/tezos-admin-client.rb
build_bottle ./Formula/tezos-baker-011-PtHangz2.rb
build_bottle ./Formula/tezos-baker-012-PsiThaCa.rb
build_bottle ./Formula/tezos-client.rb
build_bottle ./Formula/tezos-codec.rb
build_bottle ./Formula/tezos-endorser-011-PtHangz2.rb
build_bottle ./Formula/tezos-node.rb
build_bottle ./Formula/tezos-sandbox.rb
build_bottle ./Formula/tezos-signer.rb

brew uninstall ./Formula/tezos-sapling-params.rb
# https://github.com/Homebrew/brew/pull/4612#commitcomment-29995084
for bottle in ./*.bottle.*; do
    mv "$bottle" "${bottle/--/-}"
done
