#! /usr/bin/env bash
# SPDX-FileCopyrightText: 2021 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ

# This script signs all commits in the current 'BUILDKITE_BRANCH'

set -e

git config user.name "serokell-bot" # necessary for pushing
git config user.email "tezos-packaging@serokell.io"
git fetch --all
# We call this script only after a commit was pushed to the given branch, so it's safe to switch to it
git switch "$BUILDKITE_BRANCH"
git reset --hard origin/"$BUILDKITE_BRANCH"

# Find if there are unsigned commits in the current branch
# If there are grep matches then there are unsigned commits
if git log --pretty="format:%G?" "origin/$BUILDKITE_PIPELINE_DEFAULT_BRANCH..$BUILDKITE_BRANCH" --first-parent | grep "N$"; then
  echo "Found unsigned commits"
  # Try to sign and push signed commits, retry in case of collision
  while : ; do
    git fetch --all
    git reset --hard origin/"$BUILDKITE_BRANCH"
    if ! git rebase --exec 'git commit --amend -n --gpg-sign="tezos-packaging@serokell.io" --no-edit' \
      "origin/$BUILDKITE_PIPELINE_DEFAULT_BRANCH"; then
      git rebase --abort
      exit 1
    fi
    # This should fail in case we're trying to overwrite some new commits
    ! git push --force-with-lease || break
  done
else
  echo "No unsigned commits found"
fi
