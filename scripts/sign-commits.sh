#! /usr/bin/env bash
# SPDX-FileCopyrightText: 2021 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

# This script signs all commits in the current 'BUILDKITE_BRANCH'

set -e

git config user.name "serokell-bot" # necessary for pushing
git config user.email "tezos-packaging@serokell.io"

# Try to sign and push signed commits, retry in case of collision
while : ; do
  git fetch --all
  # We call this script only after a commit was pushed to the given branch, so it's safe to switch to it
  git switch "$BUILDKITE_BRANCH"
  git reset --hard origin/"$BUILDKITE_BRANCH"
  # Find if there are unsigned commits in the current branch
  # If there are grep matches then there are unsigned commits
  if git log --pretty="format:%G?" "origin/$BUILDKITE_PIPELINE_DEFAULT_BRANCH..$BUILDKITE_BRANCH" | grep "N$"; then
    echo "Found unsigned commits"
    # Rebase through all commits in the current branch and sign them, if some of the commits are already
    # signed, a signature will be overridden
    if ! git rebase --exec 'git commit --amend -n --gpg-sign="tezos-packaging@serokell.io" --no-edit' \
      "origin/$BUILDKITE_PIPELINE_DEFAULT_BRANCH"; then
      git rebase --abort
      exit 1
    fi
    # This should fail in case we're trying to overwrite some new commits
    ! git push --force-with-lease || break
  else
    echo "No unsigned commits found"
    exit 0
  fi
done

# Branch is updated when commits are successfully signed so we exit with non-zero exit code to stop the pipeline in order
# to avoid running steps on the outdated branch revision
exit 1
