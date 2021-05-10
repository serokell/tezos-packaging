#! /usr/bin/env python3

# SPDX-FileCopyrightText: 2021 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ

import argparse, re

from yaml import FullLoader, load, dump

def check_step(step, diff):
    if "only_changes" not in step:
        return True
    else:
        changes_regexes = step["only_changes"]
        for regex in changes_regexes:
            for diff_file in diff:
                r = re.compile(regex)
                match = r.match(diff_file)
                if match is not None:
                    return True
        return False

def remove_only_changes(steps):
    for step in steps:
        if type(step) != str:
            step.pop("only_changes", None)
    return steps

parser = argparse.ArgumentParser()
parser.add_argument("--pipeline", required=True)
parser.add_argument("--git-diff", required=True)
parser.add_argument("--output", required=True)
args = parser.parse_args()

splitted_diff = args.git_diff.strip().split('\n')

pipeline = load(open(args.pipeline, 'r'), Loader=FullLoader)
res = list(map(lambda x: check_step(x, splitted_diff), pipeline["steps"]))
pipeline["steps"] = remove_only_changes([x for x in pipeline["steps"] if check_step(x, splitted_diff)])
with open(args.output, 'w') as f:
    dump(pipeline, f)
