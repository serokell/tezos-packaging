<!--
   - SPDX-FileCopyrightText: 2019 TQ Tezos <https://tqtezos.com/>
   -
   - SPDX-License-Identifier: LicenseRef-MIT-TQ
   -->

# Tezos packaging

[![Build status](https://badge.buildkite.com/e899e9e54babcd14139e3bd4381bad39b5d680e08e7b7766d4.svg?branch=master)](https://buildkite.com/serokell/tezos-packaging)

This repo provides various form of distribution for tezos-related executables:
* `tezos-client`
* `tezos-admin-client`
* `tezos-node`
* `tezos-baker`
* `tezos-accuser`
* `tezos-endorser`
* `tezos-signer`
* `tezos-codec`
* `tezos-sandbox`

Daemon binaries (as well as packages for them) have suffix that defines their target protocol,
e.g. `tezos-baker-010-PtGRANAD` can be used only on the chain with 010 protocol.

Other binaries can be used with all protocols if they're new enough. E.g.
010 protocol is supported only from `v9.2`. `tezos-node` can be set up to run
different networks, you can read more about this in [this article](https://tezos.gitlab.io/user/multinetwork.html).

## Table of contents

* [Static linux binaries](#static-linux)
* [Native Ubuntu packages](#ubuntu)
  * [Ubuntu packages on Raspberry Pi OS](#raspberry)
* [Native Fedora packages](#fedora)
* [Other linux](#linux)
* [Brew tap for macOS](#macos)
* [Systemd services for Tezos binaries](#systemd)
* [Building instructions](#building)
* [Setting up baking instance on Ubuntu](#baking-on-ubuntu)

<a name="static-linux"></a>
## Obtain binaries from github release

Recomended way to get these binaries is to download them from assets from github release.
Go to the [latest release](https://github.com/serokell/tezos-packaging/releases/latest)
and download desired assets.

Some of the individual binaries contain protocol name to determine
with which protocol binary is compatible with. If this is not the
case, then consult release notes to check which protocols are
supported by that binary.

<a name="ubuntu"></a>
## Ubuntu Launchpad PPA with `tezos-*` binaries

If you are using Ubuntu you can use PPA in order to install `tezos-*` executables.
E.g, in order to do install `tezos-client` or `tezos-baker` run the following commands:
```
sudo add-apt-repository ppa:serokell/tezos && sudo apt-get update
sudo apt-get install tezos-client
# dpkg-source prohibits uppercase in the packages names so the protocol
# name is in lowercase
sudo apt-get install tezos-baker-010-ptgranad
```
Once you install such packages the commands `tezos-*` will be available.

<a name="raspberry"></a>
### Ubuntu packages on Raspberry Pi OS

If you have a Raspberry Pi running the 64bit version of the official OS, you can
use the Lauchpad PPA to install `tezos-*` executables on it as well.

You can add the PPA using:
```
# Intall software properties commons
sudo apt-get install software-properties-common
# Add PPA with Tezos binaries
sudo add-apt-repository 'deb http://ppa.launchpad.net/serokell/tezos/ubuntu bionic main'
sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys 37B8819B7D0D183812DCA9A8CE5A4D8933AE7CBB
sudo apt-get update
```

And install packages with `apt-get`, e.g. for `tezos-client`:
```
sudo apt-get install tezos-client
```

<a name="fedora"></a>
## Fedora Copr repository with `tezos-*` binaries

If you are using Fedora you can use Copr in order to install `tezos-*`
executables.
E.g. in order to install `tezos-client` or `tezos-baker` run the following commands:
```
# use dnf
sudo dnf copr enable @Serokell/Tezos
sudo dnf install tezos-client
sudo dnf install tezos-baker-010-PtGRANAD

# or use yum
sudo yum copr enable @Serokell/Tezos
sudo yum install tezos-baker-010-PtGRANAD
```
Once you install such packages the commands `tezos-*` will be available.

<a name="linux"></a>
## Other Linux distros usage

Download binaries from release assets.

### `tezos-client` example

Make it executable:
```
chmod +x tezos-client
```

Run `./tezos-client` or add it to your PATH to be able to run it anywhere.

<a name="macos"></a>
## Brew tap for macOS

If you're using macOS and `brew`, you can install Tezos binaries from the taps provided
by this repository. There are two taps: one for the latest stable release of Tezos and
one for the latest release candidate of Tezos.

In order to use latest stable version run the following:
```
brew tap serokell/tezos-packaging-stable https://github.com/serokell/tezos-packaging-stable.git
```

In order to use latest release candidate version run the following:
```
brew tap serokell/tezos-packaging-rc https://github.com/serokell/tezos-packaging-rc.git
```

Once the desired tap is selected, you can install the chosen package, e.g.:
```
brew install tezos-client
```

### Building brew bottles

It's possible to provide prebuilt macOS packages for brew called bottles. They're supposed
to be built before making the new release and included to it. In order to build all bottles run
`build-bottles.sh` script:
```
./scripts/build-bottles.sh
```

Note that this might take a while, because builds don't share common parts and for each binary
dependencies are compiled from scratch. Once the bottles are built, the corresponding sections in the
formulas should be updated. Also, bottles should be uploaded to the release artifacts.

<a name="systemd"></a>
## Background services for `tezos-node` and daemons

### Systemd units on Ubuntu or Fedora

`tezos-node`, `tezos-accuser-<proto>`, `tezos-baker-<proto>`,
`tezos-endorser-<proto>`, and `tezos-signer` packages have systemd files included to the
Ubuntu and Fedora packages.

As an addition, `tezos-baking` package provides `tezos-baking-<network>` services that orchestrate
systemd units for `tezos-node`, `tezos-baker-<proto>`, and `tezos-endorser-<proto>`.
Configuration files for these services are located in `/etc/default/tezos-baking-<network>`.

Once you've installed the packages with systemd unit, you can run the service
with the binary from the package using the following command:
```
systemctl start <package-name>.service
```
To stop the service run:
```
systemctl stop <package-name>.service
```

Each service has configuration file located in `/etc/default`. Default
configurations can be found [here](docker/package/defaults/).

Files created by the services will be located in `/var/lib/tezos/` by default.
`tezos-{accuser, baker, endorser}-<protocol>` services can have configurable
data directory.

`tezos-{accuser, endorser}` have configurable node address, so that they can be used with both
remote and local node.

### Launchd services on macOS

`tezos-accuser-<proto>`, `tezos-baker-<proto>`, `tezos-endorser-<proto>` formulas
provide backround services for running the corresponding daemons.

Since `tezos-node` and `tezos-signer` need multiple services they are provided
in dedicated meta-formulas. These formulas don't install any binaries and only add
background services.

Formulas with `tezos-node` background services:
* `tezos-node-mainnet`

Formulas with `tezos-signer` background services:
* `tezos-signer-http`
* `tezos-signer-https`
* `tesos-signer-tcp`
* `tezos-signer-unix`

To start the service: `brew services start <formula>`.

To stop the service: `brew services stop <formula>`.

All of the brew services have various configurable env variables. These variables
can be changed in the corresponding `/usr/local/Cellar/tezos-signer-tcp/<version>/homebrew.mxcl.<formula>.plist`.
Once the configuration is updated, you should restart the service:
`brew services restart <formula>`.

Note, that all services are run as a user agents, thus they're stopped after the logout.

### Systemd units on other Linux systems

If you're not using Ubuntu or Fedora you can still construct systemd units for binaries
from scratch.

For this you'll need `.service` file to define systemd service. The easiest way
to get one is to run [`gen_systemd_service_file.py`](gen_systemd_service_file.py).
You should specify service name as an argument. Note that there are three
predefined services for `tezos-node`: `tezos-node-{mainnet, florencenet, granadanet}`.

E.g.:
```
./gen_systemd_service_file.py tezos-node-mainnet
# or
./gen_systemd_service_file.py tezos-baker-010-PtGRANAD
```
After that you'll have `.service` file in the current directory.

Apart from `.service` file you'll need service startup script and default configuration
file, they can be found in [`scripts`](./docker/package/scripts) and
[`defaults`](./docker/package/defaults) folders respectively.


### Multiple similar systemd services

It's possible to run multiple same services, e.g. two `tezos-node`s that run different
networks.

`tezos-node` packages provide multiple services out of the box:
`tezos-node-florencenet`, `tezos-node-granadanet`, and `tezos-node-mainnet` that run
`florencenet`, `granadanet`, and `mainnet` networks respectively.

In order to start it run:
```
systemctl start tezos-node-<network>
```

Also, there are `tezos-node-<network>` binary aliases that are equivalent to
```
TEZOS_NODE_DIR="<DATA_DIR from tezos-node-<network>.service>" tezos-node
```

In addition to node services where the config is predefined to a specific network
(e.g. `tezos-node-mainnet` or `tezos-node-florencenet`), it's possible to run `tezos-node-custom`
service and provide a path to the custom node config file via the
`CUSTOM_NODE_CONFIG` variable in the `tezos-node-custom.service` file.

Another case for running multiple similar systemd services is when one wants to have
multiple daemons that target different protocols.
Since daemons for different protocols are provided in the different packages, they will
have different service files. The only thing that needs to be changed is config file.
One should provide desired node address, data directory for daemon files and node directory
(however, this is the case only for baker daemon).

`tezos-signer` package provides four services one for each mode in which signing daemon can run:
* Over TCP socket (`tezos-signer-tcp.service`).
* Over UNIX socker (`tezos-signer-unix.service`).
* Over HTTP (`tezos-signer-http.service`).
* Over HTTPS (`tezos-signer-https.service`)
Each signer service has dedicated config file in e.g. `/etc/default/tezos-signer-{mode}`.

<a name="building"></a>
## Build Instructions

This repository provides two distinct ways for building and packaging tezos binaries:
* [Docker-based](./docker/README.md)
* [Nix-based](./nix/README.md)

<a name="baking-on-ubuntu"></a>
## Setting up baking instance on Ubuntu

Read [the article](./docs/baking.md) to find out an easy way to set up
baking instance on Ubuntu using packages provided by our launchpad PPA.

For ease of use, a CLI wizard is provided within the `tezos-baking` package, designed to query all
necessary configuration options and use the answers to automatically set up a baking instance.

To use it, install the `tezos-baking` package for Ubuntu and run `tezos-setup-wizard`.

## For Contributors

Please see [CONTRIBUTING.md](.github/CONTRIBUTING.md) for more information.

## About Serokell

This repository is maintained with ❤️ by [Serokell](https://serokell.io/).
The names and logo for Serokell are trademark of Serokell OÜ.

We love open source software! See [our other projects](https://serokell.io/community?utm_source=github)
or [hire us](https://serokell.io/hire-us?utm_source=github) to design, develop and grow your idea!
