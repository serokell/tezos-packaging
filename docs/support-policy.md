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
* 20.04 LTS (Focal Fossa)
* 22.04 LTS (Jammy Jellyfish)
* 24.04 LTS (Noble Numbat)

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
* Fedora 40
* Fedora 41

There are packages for `x86_64` and `aarch64` architectures.

## macOS brew formulae

Brew formulae provided by `tezos-packaging` aim to support all maintained macOS versions, currently:
* macOS 13 (Ventura)
