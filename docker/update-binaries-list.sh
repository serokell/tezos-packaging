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

python3 -m docker.package.update-binaries-list

git add tests/binaries.json
if [ -n "$(git diff --staged)" ]; then
    git commit -m "Updated binaries for $BUILDKITE_TAG release" --gpg-sign="tezos-packaging@serokell.io"
    git push --set-upstream origin "$branch"
    gh pr create -B PruStephan/tmp -t "Update list of binaries for $BUILDKITE_TAG" -F ../.github/binaries_list_update_pull_request.md
else
    echo "Git diff is empty. Nothing to commit."
fi

