<!--
   - SPDX-FileCopyrightText: 2019 TQ Tezos <https://tqtezos.com/>
   -
   - SPDX-License-Identifier: MPL-2.0
   -->

# Tezos packaging

[![Build status](https://badge.buildkite.com/e899e9e54babcd14139e3bd4381bad39b5d680e08e7b7766d4.svg)](https://buildkite.com/serokell/tezos-packaging?branch=master)

This repo provides various form of distribution for tezos-related executables
(`tezos-client`, `tezos-client-admin`, `tezos-node`, `tezos-baker`,
`tezos-accuser`, `tezos-endorser`, `tezos-signer` and `tezos-protocol-compiler`).

## Build Instructions

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
binaries. Once you install such packages the commands `tezos-*` will be available.

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
binaries. Once you install such packages the commands `tezos-*` will be available.

## Obtain binary or packages from CI

If you don't want to build these files from scratch, you can download artifacts
produced by the CI. Go to the [latest master build](https://buildkite.com/serokell/tezos-packaging/builds/latest?branch=master),
click on `build and package` stage, choose `Artifacts` section and download files by clcking on the filenames.

## Ubuntu (Debian based distros) usage

### Install `.deb` package

Build or download `.deb` file from the CI and double-click on it or run:
```
sudo apt install <path to deb file>
```

### Use PPA with `tezos-*` binaries

Also if you are using Ubuntu you can use PPA in order to install `tezos-*` executables.
E.g, in order to do install `tezos-client` run the following commands:
```
sudo add-apt-repository ppa:serokell/tezos && sudo apt-get update
sudo apt-get install tezos-client-mainnet
sudo apt-get install tezos-client-babylonnet
```

## Fedora (Red Hat) usage


### Install `.rpm` package

Build or download `.rpm` file from the CI and double-click on it or run:
```
sudo yum localinstall <path to the rpm file>
```
### Use copr package with `tezos-*` binaries

Also if you are using Fedora you can use Copr in order to install `tezos-*`
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

## Other Linux distros usage

Build static `tezos-*` binary or download it from the CI.

### `tezos-client` example

Make it executable:
```
chmod +x tezos-client
```

Run `./tezos-client` or add it to your PATH to be able to run it anywhere.
## For Contributors

Please see [CONTRIBUTING.md](.github/CONTRIBUTING.md) for more information.

## About Serokell

This repository is maintained with ❤️ by [Serokell](https://serokell.io/).
The names and logo for Serokell are trademark of Serokell OÜ.

We love open source software! See [our other projects](https://serokell.io/community?utm_source=github) or [hire us](https://serokell.io/hire-us?utm_source=github) to design, develop and grow your idea!
