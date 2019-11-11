<!--
   - SPDX-FileCopyrightText: 2019 TQ Tezos <https://tqtezos.com/>
   -
   - SPDX-License-Identifier: MPL-2.0
   -->

# `tezos-client`

`tezos-client` is CLI tool used for interaction with Tezos blockchain.
This repo contains nix expression for building staticically linked
tezos-client binaries that can be used with remote tezos nodes without
using `babylonnet.sh` or `mainnet.sh` scripts.

## Build Instructions

Run `nix-build -A tezos-client-static -o tezos-static`
to build staticically linked `tezos-client` executable.

Run `nix-build -A tezos-client-{rpm, deb}-package -o tezos-client-package` in order
to build native `.rpm` or `.deb` package for RedHat and Debiab-based distros.

## `tezos-client` usage

Run `tezos-client [global options] command [command options]`.

Run `tezos-client man` to get more information.

## For Contributors

Please see [CONTRIBUTING.md](.github/CONTRIBUTING.md) for more information.

## About Serokell

This repository is maintained and funded with ❤️ by [Serokell](https://serokell.io/).
The names and logo for Serokell are trademark of Serokell OÜ.

We love open source software! See [our other projects](https://serokell.io/community?utm_source=github) or [hire us](https://serokell.io/hire-us?utm_source=github) to design, develop and grow your idea!
