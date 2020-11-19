#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2019 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ

files=$(git ls-files -- . ':!:*.patch' | xargs grep --files-with-matches --binary-files=without-match '[[:blank:]]$')
if [[ ! -z $files ]];then
  echo '  Files with trailing whitespace found:'
  for f in "${files[@]}"; do
    echo "  * $f"
  done
  exit 1
fi
