<!--
   - SPDX-FileCopyrightText: 2022 Oxhead Alpha
   - SPDX-License-Identifier: LicenseRef-MIT-OA
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
* 22.04 LTS (Jammy Jellyfish)

There are packages for `arm64` and `amd64` architectures.

## Debian packages

We aim to provide packages for all [debian releases](https://www.debian.org/releases/),
which match the supported Ubuntu releases.

Currently, these are versions:
* Debian 11 (bullseye)
* Debian 10 (buster)

There are packages for `arm64` and `amd64` architectures.

## Fedora packages

We aim to provide packages for all [currently supported Fedora releases](https://docs.fedoraproject.org/en-US/releases/).

Currently, these are versions:
* Fedora 34
* Fedora 35

There are packages for `x86_64` and `aarch64` architectures.

## macOS brew formulae

Brew formulae provided by `tezos-packaging` aim to support all maintained macOS versions:
* macOS 10.15 (Catalina)
* macOS 11 (Big Sur)
* macOS 12 (Monterey)

Unfortunately, the ability to provide pre-compiled brew bottles for formulae has
a hard dependency on the available build infrastructure. At the moment, the only macOS
versions for which we provide brew bottles are:
* macOS 11 (Big Sur) both `x86_64` and `arm64`
* macOS 10.15 (Catalina) only `x86_64`
