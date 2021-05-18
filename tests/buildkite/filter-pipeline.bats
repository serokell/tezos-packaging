#!/usr/bin/env bats

# SPDX-FileCopyrightText: 2021 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ

function setup() {
  src="tests/buildkite/pipeline-raw.yml"
  filter_script=".buildkite/filter-pipeline.py"
}

@test "trigger steps A and X" {
  "$filter_script" --pipeline "$src" --git-diff "A" --output tests/buildkite/pipeline.yml
  diff tests/buildkite/pipeline.yml tests/buildkite/golden/pipeline-A.yml
}

@test "trigger steps C and X" {
  "$filter_script" --pipeline "$src" --git-diff "C" --output tests/buildkite/pipeline.yml
  diff tests/buildkite/pipeline.yml tests/buildkite/golden/pipeline-C.yml
}

@test "trigger steps G and X" {
  "$filter_script" --pipeline "$src" --git-diff "G" --output tests/buildkite/pipeline.yml
  diff tests/buildkite/pipeline.yml tests/buildkite/golden/pipeline-G.yml
}

@test "trigger only step X" {
  "$filter_script" --pipeline "$src" --git-diff "" --output tests/buildkite/pipeline.yml
  diff tests/buildkite/pipeline.yml tests/buildkite/golden/pipeline-X.yml
}

function teardown() {
  rm tests/buildkite/pipeline.yml
}
