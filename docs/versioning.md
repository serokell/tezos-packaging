<!--
   - SPDX-FileCopyrightText: 2021 Oxhead Alpha
   - SPDX-License-Identifier: LicenseRef-MIT-OA
   -->

# Versioning

`tezos-packaging` follows all Octez releases, both stable and candidates.

Packages from our releases provide addinional functionality (e.g. systemd services
in Ubuntu and Fedora package or brew formulae with launchd services).
This additional functionality may change within the same upstream version.

In order to track this, our GitHub releases and packages use
the following RPM-like versioning scheme: `<name>-<version>-<release>`:
* `<name>` is used to mention which Octez binary is packaged.
* `<version>` is used to reference the packaged upstream version.
* `<release>` is used to reflect changes in additional packages functionality.

## GitHub releases

We provide GitHub releases for stable upstream releases and pre-releases for release candidates.

In our GitHub repository we use tags in which `<name>-` part is ommited.

E.g. `v11.0-1` is the first `tezos-packaging` release within the `v11.0` upstream stable release,
or `v11.0-rc2-2` for the second `tezos-packaging` release within the `v11.0-rc2` upstream release candidate.

GitHub {pre-}releases contain static binaries and brew bottles compiled from the given
upstream source version.

## Ubuntu packages

Ubuntu packages use a slightly different versioning scheme, which follows
the [Debian versioning policy](https://www.debian.org/doc/debian-policy/ch-controlfields.html#version):
`<name>-<version>-0ubuntu<release>~<ubuntu-version>`.

E.g. `tezos-client-11.0+no-adx-0ubuntu1~focal`, where `focal` is `20.04 LTS`.

We use different PPA repositories for stable and release candidate Ubuntu packages.
You can read more about this in the [doc about Ubuntu packages](./distros/ubuntu.md).

## Fedora packages

We use different Copr projects for stable and release candidate Fedora packages.
You can read more about this in the [doc about Fedora packages](./distros/fedora.md).

## Brew formulae

We use two distinct repository mirrors to provide stable and release candidate brew formulae.
You can read more about this in the [doc about macOS packaging](./distros/macos.md).
