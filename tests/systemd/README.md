<!--
   - SPDX-FileCopyrightText: 2022 Oxhead Alpha
   -
   - SPDX-License-Identifier: LicenseRef-MIT-OA
   -->

# Testing systemd services

## Prerequisites

1) [Vagrant](https://www.vagrantup.com/).
2) [`libvirt`](https://libvirt.org/) and [`qemu`](https://www.qemu.org/).
3) `.deb` packages with Octez binaries and systemd services to test.

## Getting `.deb` packages

The easiest way to get `.deb` packages with systemd services for testing
is to download static Octez binaries and build `.deb` packages using them
instead of compiling Octez from scratch for each package.
Refer to [this doc](../../docker/README.md#packages-from-statically-linked-binaries)
for building instructions.

## Testing

Run
```sh
vagrant --packages-directory="<dir>" up --provider=libvirt
```

Where 'PACKAGES_DIRECTORY' is the directory with `.deb` packages.

Tests are run during VM provisioning, so `vagrant up` is expected to fail
in case some tests are failing.

To clean up the state after VM test run:
```sh
vagrant --packages-directory="<dir>" destroy --force
```
