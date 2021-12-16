<!--
   - SPDX-FileCopyrightText: 2021 TQ Tezos <https://tqtezos.com/>
   -
   - SPDX-License-Identifier: LicenseRef-MIT-TQ
   -->
# Packages support policy

`tezos-packaging` provides packages for Ubuntu, Fedora and macOS for each stable and release-candidate
version of Octez.

This document describes which versions of the aforementioned OSes are targeted
by our packages.

## Ubuntu packages

We aim to provide packages for all [Ubuntu LTS releases](https://wiki.ubuntu.com/Releases)
supported by Canonical.

Currently, these are versions:
* 18.04 LTS (Bionic Beaver)
* 20.04 LTS (Focal Fossa)

When feasible, we also provide support for non-LTS versions on request from the users.
Currently:
* 21.04 (Hirsute Hippo) - requested in [#212](https://github.com/serokell/tezos-packaging/issues/212)

There are packages for `arm64` and `amd64` architectures.

## Fedora packages

We aim to provide packages for all [currently supported Fedora releases](https://docs.fedoraproject.org/en-US/releases/).

Currently, these are versions:
* Fedora 34, both `x86_64` and `aarch64`
* Fedora 35, only `aarch64`. `x86_64` is currently unsupported due to [tezos/#1449](https://gitlab.com/tezos/tezos/-/issues/1449)

There are packages for `x86_64` and `aarch64` architectures.

## macOS brew formulae

Brew formulae provided by `tezos-packaging` aim to support all maintained macOS versions:
* macOS 10.15 (Catalina)
* macOS 11 (Big Sur)
* macOS 12 (Monterey)

Unfortunately, an ability to provide pre-compiled brew bottles for formulae has
a hard dependency on the available build infrastructure. At the moment, the only macOS
versions for which we provide brew bottles are:
* macOS 11 (Big Sur) both `x86_64` and `arm64`
* macOS 10.15 (Catalina) only `x86_64`
