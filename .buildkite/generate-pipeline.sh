#! /usr/bin/env nix-shell
#! nix-shell ../default.nix -A devShells.x86_64-linux.buildkite -i bash

# SPDX-FileCopyrightText: 2021 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ

set -euo pipefail

git fetch origin master

diff="$(git diff origin/master...HEAD --name-only)"

# Diff with the master branch is empty when we're in the master branch,
# so we're using 'git diff --name-only HEAD HEAD~1' instead
if [[ -z $diff ]]; then
  diff="$(git diff --name-only HEAD~1 HEAD)"
fi

.buildkite/filter-pipeline.py --pipeline .buildkite/pipeline-raw.yml \
  --git-diff "$diff" --output .buildkite/pipeline.yml
