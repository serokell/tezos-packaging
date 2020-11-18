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

Daemon binaries (as well as packages for them) have suffix that defines their target protocol,
e.g. `tezos-baker-007-PsDELPH1` can be used only on the chain with 007 protocol.

Other binaries can be used with all protocols if they're new enough. E.g.
007 protocol is supported only from `v7.4`. `tezos-node` can be set up to run
different networks, you can read more about this in [this article](https://tezos.gitlab.io/user/multinetwork.html).

## Obtain binaries from github release

Recomended way to get these binaries is to download them from assets from github release.
Go to the [latest release](https://github.com/serokell/tezos-packaging/releases/latest)
and download desired assets.

Some of the individual binaries contain protocol name to determine
with which protocol binary is compatible with. If this is not the
case, then consult release notes to check which protocols are
supported by that binary.

## Ubuntu Launchpad PPA with `tezos-*` binaries

If you are using Ubuntu you can use PPA in order to install `tezos-*` executables.
E.g, in order to do install `tezos-client` or `tezos-baker` run the following commands:
```
sudo add-apt-repository ppa:serokell/tezos && sudo apt-get update
sudo apt-get install tezos-client
# dpkg-source prohibits uppercase in the packages names so the protocol
# name is in lowercase
sudo apt-get install tezos-baker-007-psdelph1
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
sudo dnf install tezos-baker-007-PsDELPH1

# or use yum
sudo yum copr enable @Serokell/Tezos
sudo yum install tezos-baker-007-PsDELPH1
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

## Systemd units for `tezos-node` and daemons

### Systemd units on Ubuntu or Fedora

`tezos-node`, `tezos-accuser-<proto>`, `tezos-baker-<proto>` and
`tezos-endorser-<proto>` packages have systemd files included to the
Ubuntu and Fedora packages.

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

### Systemd units on other systems

If you're not using Ubuntu or Fedora you can still construct systemd units for binaries
from scratch.

For this you'll need `.service` file to define systemd service. The easiest way
to get one is to run [`gen_systemd_service_file.py`](gen_systemd_service_file.py).
You should specify service name as an argument. Note that there are three
predefined services for `tezos-node`: `tezos-node-{mainnet, delphinet}`.

E.g.:
```
./gen_systemd_service_file.py tezos-node-mainnet
# or
./gen_systemd_service_file.py tezos-baker-007-PsDELPH1
```
After that you'll have `.service` file in the current directory.

Apart from `.service` file you'll need service startup script and default configuration
file, they can be found in [`scripts`](./docker/package/scripts) and
[`defaults`](./docker/package/defaults) folders respectively.


### Multiple similar systemd services

It's possible to run multiple same services, e.g. two `tezos-node`s that run different
networks.

`tezos-node` packages provide three services out of the box:
`tezos-node-delphinet` and `tezos-node-mainnet` that run
`delphinet` and `mainnet` networks respectively.

In order to start it run:
```
systemctl start tezos-node-<network>
```

Another case for running multiple similar systemd services is when one wants to have
multiple daemons that target different protocols.
Since daemons for different protocols are provided in the different packages, they will
have different service files. The only thing that needs to be changed is config file.
One should provide desired node address, data directory for daemon files and node directory
(however, this is the case only for baker daemon).

## Build Instructions

This repository provides two distinct ways for building and packaging tezos binaries:
* [Docker-based](./docker/README.md)
* [Nix-based](./nix/README.md)

## For Contributors

Please see [CONTRIBUTING.md](.github/CONTRIBUTING.md) for more information.

## About Serokell

This repository is maintained with ❤️ by [Serokell](https://serokell.io/).
The names and logo for Serokell are trademark of Serokell OÜ.

We love open source software! See [our other projects](https://serokell.io/community?utm_source=github) or [hire us](https://serokell.io/hire-us?utm_source=github) to design, develop and grow your idea!
