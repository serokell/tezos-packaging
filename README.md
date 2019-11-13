<!--
   - SPDX-FileCopyrightText: 2019 TQ Tezos <https://tqtezos.com/>
   -
   - SPDX-License-Identifier: MPL-2.0
   -->

# `tezos-client`

[![Build status](https://badge.buildkite.com/e899e9e54babcd14139e3bd4381bad39b5d680e08e7b7766d4.svg)](https://buildkite.com/serokell/tezos-client)

`tezos-client` is CLI tool used for interaction with Tezos blockchain.
This repo contains nix expression for building staticically linked
tezos-client binaries that can be used with remote tezos nodes without
using `babylonnet.sh` or `mainnet.sh` scripts.

## Build Instructions

Run `nix-build -A tezos-client-static -o tezos-static`
to build staticically linked `tezos-client` executable.

Run `nix-build -A tezos-client-{rpm, deb}-package -o tezos-client-package` in order
to build native `.rpm` or `.deb` package for Red Hat and Debian-based distros.

## Obtain binary or packages from CI

If you don't want to build these files from scratch, you can download artifacts
produced by the CI. Go to the [latest master build](https://buildkite.com/serokell/tezos-client/builds/latest?branch=master),
click on `build and package` stage, choose `Artifacts` section and download files by clcking on the filenames.

## Ubuntu (Debian based distros) usage

### Install downloaded `.deb` package

Download `.deb` file from the CI and double-click on it or run:
```
sudo apt install <path to deb file>
```

### Use PPA with `tezos-client`

Also if you are using Ubuntu you can use PPA in order to install `tezos-client`.
In order to do that run the following commands:
```
sudo add-apt-repository ppa:serokell/tezos && sudo apt-get update
sudo apt-get install tezos-client
```

## Fedora (Red Hat) usage

Download `.rpm` file from the CI and double-click on it or run:
```
sudo yum localinstall <path to the rpm file>
```

## Other Linux distros usage

Download statically built `tezos-client` binary from the CI.
Make it executable:
```
chmod +x tezos-client
```

Run `./tezos-client` or add it to your PATH to be able to run it anywhere.

## `tezos-client` usage

Run `tezos-client [global options] command [command options]`.

Run `tezos-client man` to get more information.

## For Contributors

Please see [CONTRIBUTING.md](.github/CONTRIBUTING.md) for more information.

## About Serokell

This repository is maintained with ❤️ by [Serokell](https://serokell.io/).
The names and logo for Serokell are trademark of Serokell OÜ.

We love open source software! See [our other projects](https://serokell.io/community?utm_source=github) or [hire us](https://serokell.io/hire-us?utm_source=github) to design, develop and grow your idea!
