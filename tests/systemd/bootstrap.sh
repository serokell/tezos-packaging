#! /usr/bin/env bash
# SPDX-FileCopyrightText: 2022 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

set -e

dpkg -i ./out/tezos-client*~focal_amd64.deb
dpkg -i ./out/tezos-baker*~focal_amd64.deb
dpkg -i ./out/tezos-accuser*~focal_amd64.deb
dpkg -i ./out/tezos-node*~focal_amd64.deb
dpkg -i ./out/tezos-signer*~focal_amd64.deb
dpkg -i ./out/tezos-baking*~focal_amd64.deb
