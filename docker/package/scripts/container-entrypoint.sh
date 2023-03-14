#!/usr/bin/env bash

# SPDX-FileCopyrightText: 2023 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

set -euo pipefail

IFS=' ' read -ra cmd_args <<<"${args:-}"
builder -m package.package_generator "${cmd_args[@]}"
