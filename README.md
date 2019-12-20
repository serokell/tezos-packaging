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

## Obtain binaries from github release

Recomended way to get these binaries is to download them from assets from github release.
Go to the [latest release](https://github.com/serokell/tezos-packaging/releases/latest)
and download desired assets.

We provide both individual and archived binaries from master branch sources
in order to be able to have static links for these binaries, also make it convenient
to download single binary or obtain all binaries in one click.

Some of the individual binaries contain protocol name
to determine with which protocol binary is compatible with, specifically `005_PsBabyM1`
protocol is currently used in `mainnet` and `babylonnet`, `006_PsCARTHA` protocol
is currently used in `carthagenet`.

Binaries without protocol name can be used with any network. E.g. `tezos-node` has `--network`
option ([more information](http://tezos.gitlab.io/user/multinetwork.html) about multinetwork node)
and `tezos-client` is compatible with any network node (Note that this is true only for binaries
built from master branch sources).

Contents of release:
* `tezos-*-005-PsBabyM1` static binaries for 005 protocol.
* `tezos-*-006-PsCARTHA` static binaries for 006 protocol.
* `tezos-*` static binaries that can be used with any protocol.
* `binaries-<revision>.tar.gz` archive with all binaries made from
particular master branch revision.
* License file from [tezos repository](https://gitlab.com/tezos/tezos/).

## Ubuntu Launchpad PPA with `tezos-*` binaries

If you are using Ubuntu you can use PPA in order to install `tezos-*` executables.
E.g, in order to do install `tezos-client` or `tezos-baker` run the following commands:
```
sudo add-apt-repository ppa:serokell/tezos && sudo apt-get update
sudo apt-get install tezos-client
# dpkg-source prohibits uppercase in the packages names so the protocol
# name is in lowercase
sudo apt-get install tezos-baker-005-psbabym1
```
Once you install such packages the commands `tezos-*` will be available.

## Fedora Copr repository with `tezos-*` binaries

If you are using Fedora you can use Copr in order to install `tezos-*`
executables.
E.g. in order to install `tezos-client` or `tezos-baker` run the following commands:
```
# use dnf
sudo dnf copr enable @Serokell/Tezos
sudo dnf install tezos-client
sudo dnf install tezos-baker-005-PsBabyM1

# or use yum
sudo yum copr enable @Serokell/Tezos
sudo yum install tezos-baker-005-PsBabyM1
```
Once you install such packages the commands `tezos-*` will be available.

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

Run one the following command:
```
nix-build -A binaries -o binaries
```

Or use Makefile:
```bash
make binaries
```

To produce `tar.gz` archive tezos binaries.

<a name="deb"></a>
### Ubuntu `.deb` packages

Run the following command:
```
nix-build -A deb-packages -o deb-packages --arg timestamp $(date +"%Y%m%d%H%M")
```

Or use Makefile:
```bash
make deb-packages #build deb packages
```

To build `.deb` packages with tezos binaries.

Once you built them, you can install `.deb` packages using the following command:
```
sudo apt install <path to deb file>

### Publish packages on Launchpad PPA

In order to publish packages on PPA you will have to build source packages,
you can do this by running the following commands:
```
nix-build -A deb-source-packages -o deb-source-packages \
--arg builderInfo "\"Roman Melnikov <roman.melnikov@serokell.io>\"" \
--arg timestamp "$(date +\"%Y%m%d%H%M\")" --arg date "\"$(date -R)\""
# Note that buildInfo should contain information about user how is capable
# in publishing packages on PPA

# Copy files from /nix/store
mkdir -p source-packages
cp deb-source-packages/* source-packages
# Sign *.changes files with your gpg key, which should be known
# for Launchpad
debsign source-packages/*.changes
# dput all packages to PPA repository
dput ppa:serokell/tezos source-package/*.changes
```

### Fedora `.rpm` packages

Run one of the following commands:
```
nix-build -A rpm-packages -o rpm-packages --arg timestamp $(date +"%Y%m%d%H%M")
```

Or use Makefile:
```bash
make rpm-packages #build rpm packages
```

To build `.rpm` packages with tezos binaries.

Once you built them, you can install `.rpm` packages using the following command:
```
sudo yum localinstall <path to the rpm file>
```

### Publish packages on Fedora Copr

In order to publish packages on Copr you will have to build source packages,
you can do this by running the following command:
```
nix-build -A rpm-source-packages -o rpm-source-packages \
--arg timestamp "$(date +\"%Y%m%d%H%M\")"
# Copy files from /nix/store
mkdir -p source-packages
cp rpm-source-packages/* source-packages
```
After this `source-packages` directory will contain `.src.rpm` packages which
can be uploaded to Copr repository.

## For Contributors

Please see [CONTRIBUTING.md](.github/CONTRIBUTING.md) for more information.

## About Serokell

This repository is maintained with ❤️ by [Serokell](https://serokell.io/).
The names and logo for Serokell are trademark of Serokell OÜ.

We love open source software! See [our other projects](https://serokell.io/community?utm_source=github) or [hire us](https://serokell.io/hire-us?utm_source=github) to design, develop and grow your idea!
