<!--
   - SPDX-FileCopyrightText: 2021 TQ Tezos <https://tqtezos.com/>
   -
   - SPDX-License-Identifier: LicenseRef-MIT-TQ
   -->
# Fedora Copr repository with `tezos-*` binaries

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

## Systemd services from Fedora packages

Some of the packages provide background `systemd` services, you can read more about them
[here](../systemd.md#ubuntu-and-fedora).
