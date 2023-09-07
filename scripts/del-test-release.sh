#!/usr/bin/env bash
# shellcheck shell=bash
# SPDX-FileCopyrightText: 2023 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

set -euo pipefail

gh release delete test-release --yes || true
