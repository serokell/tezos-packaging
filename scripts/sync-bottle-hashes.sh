#! /usr/bin/env bash
# SPDX-FileCopyrightText: 2021 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ

# This script takes the new tag and the OS name as its arguments
# and handles git shenanigans related to syncing two pipelines over a common branch.

set -e

if [ -z "$1" ] || [ -z "$2" ]; then
    echo "Please call this script with the release tag and the OS name."
    exit 1
fi

git config user.name "Serokell CI bot" # necessary for pushing
git config user.email "tezos-packaging@serokell.io" # this address matches the one that is used for signing packages
git fetch --all

branch_name="auto/update-brew-formulae-$1"

# Git doesn't have an easy way to check out a branch regardless of whether it exists.
if ! git switch "$branch_name"; then
    git switch -c "$branch_name"
    git push --set-upstream origin "$branch_name"
fi

# Try to add hashes and push changes upstream. If there is a collision precisely at the time of
# pushing, that means the other pipeline has raced this one to push. Reset to origin and try again.
while : ; do
    git fetch --all
    git reset --hard origin/"$branch_name"
    ./scripts/bottle-hashes.sh .
    git commit -a -m "[Chore] Add $1 hashes to brew formulae"
    ! git push || break
done

pr_body="Problem: we have built brew bottles for the new Octez release, but their hashes
aren't in the formulae yet.

Solution: added the hashes.
"

set +e

# We create the PR with the first push, when the other pipeline hasn't finished yet.
# That's why we 'set +e': one of the two times the command will fail.
gh pr create -B master -t "[Chore] Add bottle hashes for $1" -b "$pr_body"

exit 0
