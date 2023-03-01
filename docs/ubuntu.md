<!--
   - SPDX-FileCopyrightText: 2021 Oxhead Alpha
   - SPDX-License-Identifier: LicenseRef-MIT-OA
   -->
<a name="ubuntu"></a>
# Ubuntu Launchpad PPA with `tezos-*` binaries

If you are using Ubuntu you can use PPA in order to install `tezos-*` executables.
E.g, in order to do install `tezos-client` or `tezos-baker` run the following commands:
```
sudo add-apt-repository ppa:serokell/tezos && sudo apt-get update
sudo apt-get install tezos-client
# dpkg-source prohibits uppercase in the packages names so the protocol
# name is in lowercase
sudo apt-get install tezos-baker-013-ptjakart
```
Once you install such packages the commands `tezos-*` will be available.

## Using release-candidate packages

In order to use packages with the latest release-candidate Tezos binaries,
use `ppa:serokell/tezos-rc` PPA:
```
sudo add-apt-repository ppa:serokell/tezos-rc && sudo apt-get update
```

## `tezos-baking` package

As an addition, `tezos-baking` package provides `tezos-baking-<network>` services that orchestrate
systemd units for `tezos-node` and `tezos-baker-<proto>`.
Configuration files for these services are located in `/etc/default/tezos-baking-<network>`.

<a name="debian"></a>
## Ubuntu packages on Debian

You can add the PPA using:
```
# Install software properties commons
sudo apt-get install software-properties-common gnupg
# Add PPA with Tezos binaries
sudo add-apt-repository 'deb http://ppa.launchpad.net/serokell/tezos/ubuntu bionic main'
sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys 37B8819B7D0D183812DCA9A8CE5A4D8933AE7CBB
sudo apt-get update
```
If packages for `bionic` are not suited for your Debian version, see the
[related askubuntu thread](https://askubuntu.com/a/445496) to choose a valid one.

Then install with `apt-get`, e.g. for `tezos-client`:
```
sudo apt-get install tezos-client
```

<a name="raspberry"></a>
## Ubuntu packages on Raspberry Pi OS

If you have a Raspberry Pi running the [64bit version of the official OS](https://www.raspberrypi.com/software/operating-systems/#raspberry-pi-os-64-bit),
you can use the Launchpad PPA to install `tezos-*` executables on it as well.

You can add the PPA using:
```
# Install software properties commons
sudo apt-get install software-properties-common
# Add PPA with Tezos binaries
sudo add-apt-repository 'deb http://ppa.launchpad.net/serokell/tezos/ubuntu focal main'
sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys 37B8819B7D0D183812DCA9A8CE5A4D8933AE7CBB
sudo apt-get update
```

And install packages with `apt-get`, e.g. for `tezos-client`:
```
sudo apt-get install tezos-client
```

## Systemd services from Ubuntu packages

Some of the packages provide background `systemd` services, you can read more about them
[here](./systemd.md#ubuntu-and-fedora).
