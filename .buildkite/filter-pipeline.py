#! /usr/bin/env python3

# SPDX-FileCopyrightText: 2021 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ

# This script performs filtering of a buildkite pipeline.yml configuration
# file. The filter is based on the contents of 'only_changes' steps
# attributes.
# 'only_changes' attribute should be a list of regexes, changes in filepaths
# that match one of these regexes, should trigger the given step to run.
#
# If the current step is triggered to run and it depends on another step,
# the step we depend on is also triggered to run to provide the required
# dependencies.
# And vice versa, if the current step depends on the step which was triggered to run,
# the current step is also triggered to run to use updated dependencies in
# dependent steps.
#
# Consider the following example (lower steps depend on the higher):
#       A —
#      / \ \
#     B  C  X
#    /   |
#   D    E
#  / \ / \
# F   G  H
#
# If step 'A' is triggered to run, then all other steps will be triggered to run.
# If step 'C' is triggered to run, then steps 'A', 'E', 'H', 'G', 'D', 'B' will be triggered
# to run as well.
# If step 'G' is triggered to run, then steps 'A', 'B', 'C', 'D', 'E' will be triggered to run.
# If step 'X' is triggered to run, then step 'A' will be triggered to run
#
# You should provide 3 options in order to run this script:
# 1) '--pipeline' to provide filepath to the source pipeline configuration
#    with 'only_changes' steps attributes.
# 2) '--git-diff' to provide a list of newline-separated filepaths of files
#    that were changed. This option is usually used the following way:
#    '--git-diff "$(git diff --name-only ...)"
# 3) '--output' to provide filepath for the output pipeline configuration.
#    Required steps are skipped via 'skip: skipped due to lack of changes' attribute.
# Example:
# filter-pipeline.py --pipeline .buildkite/pipeline-raw.yml \
#   --git-diff "$(git diff --name-only origin/master...HEAD)" \
#   --output .buildkite/pipeline.yml

import argparse, re

from yaml import FullLoader, load, dump


def check_step(step, diff):
    changes_regexes = step.pop("only_changes", None)
    if changes_regexes is None:
        return True
    else:
        for regex in changes_regexes:
            r = re.compile(regex)
            for diff_file in diff:
                if r.match(diff_file) is not None:
                    return True
        return False


def dfs(name, depends_on_dict, visited):
    if name not in visited:
        visited.add(name)
        for adjacent in depends_on_dict.get(name, []):
            dfs(adjacent, depends_on_dict, visited)


# Buildkite uses 'key' attribute to determine dependencies of steps.
# Existing code uses 'label's when analyzing dependency tree, so that
# it's possible to analyze reverse dependencies as well.
# This function builds a dict that maps 'key's to 'label's
def build_key_to_label(steps):
    key_to_label = {}
    for step in steps:
        if "key" in step and "label" in step:
            key_to_label[step["key"]] = step["label"]
    return key_to_label


def build_tree(steps, key_to_label):
    depends_on_dict = {}
    depends_on_dict_rev = {}
    for step in steps:
        label = step["label"]
        depends_on = step.get("depends_on", None)
        if depends_on is not None:
            if type(depends_on) == str:
                # use 'label' from step assosiated with the given 'key'
                dependency_label = key_to_label[depends_on]
                depends_on_dict.setdefault(dependency_label, []).append(label)
                depends_on_dict_rev.setdefault(label, []).append(dependency_label)
            else:
                for dependency in depends_on:
                    if type(dependency) == str:
                        dependency_name = dependency
                    else:
                        dependency_name = dependency["step"]
                    # use 'label' from step assosiated with the given 'key'
                    dependency_label = key_to_label[dependency_name]
                    depends_on_dict.setdefault(dependency_label, []).append(label)
                    depends_on_dict_rev.setdefault(label, []).append(dependency_label)
    return depends_on_dict, depends_on_dict_rev


parser = argparse.ArgumentParser()
parser.add_argument("--pipeline", required=True)
parser.add_argument("--git-diff", required=True)
parser.add_argument("--output", required=True)
args = parser.parse_args()

splitted_diff = args.git_diff.strip().split("\n")
pipeline = load(open(args.pipeline, "r"), Loader=FullLoader)

visited = set()
visited_rev = set()

steps = pipeline["steps"]
dict_steps = list(filter(lambda x: isinstance(x, dict), steps))
key_to_label = build_key_to_label(dict_steps)
depends_on_dict, depends_on_dict_rev = build_tree(dict_steps, key_to_label)
for step in dict_steps:
    if check_step(step, splitted_diff):
        label = step["label"]
        dfs(label, depends_on_dict, visited)
        dfs(label, depends_on_dict_rev, visited_rev)

for name in visited:
    dfs(name, depends_on_dict_rev, visited_rev)

for step in dict_steps:
    label = step["label"]
    if (label not in visited) and (label not in visited_rev):
        step["skip"] = "skipped due to lack of changes"

with open(args.output, "w") as f:
    dump(pipeline, f)
