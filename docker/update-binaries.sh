#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2019 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ

bot_name="CI bot"
branch="update-binaries-list-$BUILDKITE_TAG"

git config --local user.email "hi@serokell.io"
git config --local user.name "$bot_name"
git fetch --all
git checkout -B "$branch"

python3 package/scripts/update-binaries-list.py

git add --all
git commit -m "Updated binaries for $BUILDKITE_TAG release" --gpg-sign="tezos-packaging@serokell.io"
git push --set-upstream origin "$branch"
gh pr create -B master -t "Update list of binaries for $BUILDKITE_TAG" -b "Updated list of binaries for $BUILDKITE_TAG version"
