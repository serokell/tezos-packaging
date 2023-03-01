<!--
   - SPDX-FileCopyrightText: 2021 Oxhead Alpha
   - SPDX-License-Identifier: LicenseRef-MIT-OA
   -->
# Fedora Copr repository with `tezos-*` binaries

If you are using Fedora you can use Copr in order to install `tezos-*`
executables.
E.g. in order to install `tezos-client` or `tezos-baker` run the following commands:
```
# use dnf
sudo dnf copr enable @Serokell/Tezos
sudo dnf install tezos-client
sudo dnf install tezos-baker-PtLimaPt

# or use yum
sudo yum copr enable @Serokell/Tezos
sudo yum install tezos-baker-PtLimaPt
```
Once you install such packages the commands `tezos-*` will be available.

## Using release-candidate packages

In order to use packages with the latest release-candidate Tezos binaries,
use `@Serokell/Tezos-rc` project:
```
# use dnf
sudo dnf copr enable @Serokell/Tezos-rc

# or use yum
sudo yum copr enable @Serokell/Tezos-rc
```

## Systemd services from Fedora packages

Some of the packages provide background `systemd` services, you can read more about them
[here](./systemd.md#ubuntu-and-fedora).
