<!--
   - SPDX-FileCopyrightText: 2019 TQ Tezos <https://tqtezos.com/>
   -
   - SPDX-License-Identifier: MPL-2.0
   -->

# Tezos packaging

[![Build status](https://badge.buildkite.com/e899e9e54babcd14139e3bd4381bad39b5d680e08e7b7766d4.svg?branch=master)](https://buildkite.com/serokell/tezos-packaging)

This repo provides various form of distribution for tezos-related executables
(`tezos-client`, `tezos-client-admin`, `tezos-node`, `tezos-baker`,
`tezos-accuser`, `tezos-endorser`, `tezos-signer` and `tezos-protocol-compiler`).

## Obtain binaries or packages from github release

Recomended way to get these binaries is to download them from assets from github release.
Go to the [latest release](https://github.com/serokell/tezos-packaging/releases/latest)
and download desired assets.

## Ubuntu (Debian based distros) usage

### Use PPA with `tezos-*` binaries

If you are using Ubuntu you can use PPA in order to install `tezos-*` executables.
E.g, in order to do install `tezos-client` run the following commands:
```
sudo add-apt-repository ppa:serokell/tezos && sudo apt-get update
sudo apt-get install tezos-client-mainnet
sudo apt-get install tezos-client-babylonnet
```
Once you install such packages the commands `tezos-*` will be available.

### Install `.deb` package locally

As an alternative, you can download `.deb` file from release assets
(they are located in `deb-packages.tar.gz` archive) and double-click on it or run:
```
sudo apt install <path to deb file>
```

## Fedora (Red Hat) usage

### Use copr package with `tezos-*` binaries

If you are using Fedora you can use Copr in order to install `tezos-*`
executables.
E.g. in order to install `tezos-client` run the following commands:
```
# use dnf
sudo dnf copr enable @Serokell/Tezos
sudo dnf install tezos-client-mainnet
sudo dnf install tezos-client-babylonnet

# or use yum
sudo yum copr enable @Serokell/Tezos
sudo yum install tezos-client-mainnet
sudo yum install tezos-client-babylonnet
```
Once you install such packages the commands `tezos-*` will be available.

### Install `.rpm` package

As an alternative, you can download `.rpm` file from release assets
(they are located in `rpm-packages.tar.gz` archive) and double-click on it or run:
```
sudo yum localinstall <path to the rpm file>
```

## Other Linux distros usage

Download binaries from release assets.

### `tezos-client` example

Make it executable:
```
chmod +x tezos-client
```

Run `./tezos-client` or add it to your PATH to be able to run it anywhere.

## Build Instructions

Also, you can build all these binaries and packages from scratch using nix.

### Statically built binaries

Run one of the following commands:
```
nix-build -A babylonnet-binaries -o babylonnet-binaries
nix-build -A mainnet-binaries -o mainnet-binaries
```

Or use Makefile:
```bash
make binaries #build babylonnet version of binaries
make binaries-mainnet #build mainnet version of binaries
```

To produce `tar.gz` archive with `babylonnet` or `mainnet` version of tezos
binaries.

### Ubuntu `.deb` packages

Run the following command:
```
nix-build -A deb-packages -o deb-packages --arg timestamp $(date +"%Y%m%d%H%M")
```

Or use Makefile:
```bash
make deb-packages #build deb package
```

To build `.deb` packages with `mainnet` or `babylonnet` version of tezos
binaries.

### Fedora `.rpm` packages

Run one of the following commands:
```
nix-build -A rpm-packages -o rpm-packages --arg timestamp $(date +"%Y%m%d%H%M")
```

Or use Makefile:
```bash
make rpm-packages #build rpm packages
```

To build `.rpm` packages with `mainnet` or `babylonnet` version of tezos
binaries.

## For Contributors

Please see [CONTRIBUTING.md](.github/CONTRIBUTING.md) for more information.

## About Serokell

This repository is maintained with ❤️ by [Serokell](https://serokell.io/).
The names and logo for Serokell are trademark of Serokell OÜ.

We love open source software! See [our other projects](https://serokell.io/community?utm_source=github) or [hire us](https://serokell.io/hire-us?utm_source=github) to design, develop and grow your idea!
