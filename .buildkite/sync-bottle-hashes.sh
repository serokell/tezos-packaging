#! /usr/bin/env bash
# SPDX-FileCopyrightText: 2021 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ

# This script takes the new tag and the OS name as its arguments
# and handles git shenanigans related to syncing two pipelines over a common branch.

if [ -z "$1" ] && [ -z "$2" ]; then
    git config user.name "Serokell" # necessary for pushing
    git config user.email "hi@serokell.io" # TODO: right values
    git fetch

    branch_name="auto/update-brew-formulae-$1"

    function compute_and_commit {
        ./scripts/bottle-hashes.sh .
        git commit -a -m "[Chore] Add $1 hashes to brew formulae"
    }

    commit_body="Add bottle hashes for $1

Problem: we have built brew bottles for the new Octez release, but their hashes
aren't in the formulae yet.

Solution: added the hashes.
"

    # Git doesn't have an easy way to check out a branch regardless of whether it exists.
    if git ls-remote --exit-code --heads origin "$branch_name"; then
        git switch "$branch_name"
        git pull --rebase
        compute_and_commit "$2"
        git push

        gh pr create -H -b "$commit_body"
    else
        git switch -c "$branch_name"
        compute_and_commit "$2"
        git push --set-upstream origin "$branch_name"

        # If there is a collision precisely at the time of pushing, that means the other pipeline
        # has pushed but opened the PR yet. Reset to origin and try again, this time opening a PR.
        # Once should always be enough.
        if [[ $? != 0 ]]; then
            git fetch
            git reset --hard origin/"$branch_name"
            compute_and_commit "$2"
            git push
            gh pr create -H -b "$commit_body"
        fi
    fi
else
    echo "Please call this script with the release tag and the OS name."
fi
