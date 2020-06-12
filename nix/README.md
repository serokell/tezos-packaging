<!--
   - SPDX-FileCopyrightText: 2019 TQ Tezos <https://tqtezos.com/>
   -
   - SPDX-License-Identifier: MPL-2.0
   -->

# Building and packaging tezos using nix

## Statically built binaries

In order to build all binaries run:
```bash
nix build -f. binaries
```

As an alternative you can build single binary:
```
nix build -f. binaries.tezos-client
```

This will produce `tezos-client` binary.

## Ubuntu `.deb` packages

Run the following command:
```
nix-build -A deb -o deb-packages --arg timestamp $(date +"%Y%m%d%H%M")
```

Or use Makefile:
```bash
make deb-packages #build deb packages
```

To build `.deb` packages with tezos binaries.

Once you built them, you can install `.deb` packages using the following command:
```
sudo apt install <path to deb file>
```

## Publishing packages on Launchpad PPA

In order to publish packages on PPA you will have to build source packages,
you can do this by running the following commands:
```
nix-build -A debSource -o deb-source-packages \
--arg builderInfo "\"Roman Melnikov <roman.melnikov@serokell.io>\"" \
--arg timestamp "$(date +\"%Y%m%d%H%M\")" --arg date "\"$(date -R)\"" \
--arg ubuntuVersion "\"bionic\""
# Note that buildInfo should contain information about user how is capable
# in publishing packages on PPA
# Also you can specify ubuntu version you're building packages for.
# "bionic" (18.04 LTS) is default version. Consider building packages
# for "eoan" and "xenial" as well.

# Copy files from /nix/store
mkdir -p source-packages
cp deb-source-packages/* source-packages
# Sign *.changes files with your gpg key, which should be known
# for Launchpad
debsign source-packages/*.changes
# dput all packages to PPA repository
dput ppa:serokell/tezos source-package/*.changes
```

### Fedora `.rpm` packages

Run one of the following commands:
```
nix-build -A rpm -o rpm-packages --arg timestamp $(date +"%Y%m%d%H%M")
```

Or use Makefile:
```bash
make rpm-packages #build rpm packages
```

To build `.rpm` packages with tezos binaries.

Once you built them, you can install `.rpm` packages using the following command:
```
sudo yum localinstall <path to the rpm file>
```

### Publish packages on Fedora Copr

In order to publish packages on Copr you will have to build source packages,
you can do this by running the following command:
```
nix-build -A rpmSource -o rpm-source-packages \
--arg timestamp "$(date +\"%Y%m%d%H%M\")"
# Copy files from /nix/store
mkdir -p source-packages
cp rpm-source-packages/* source-packages
```
After this `source-packages` directory will contain `.src.rpm` packages which
can be uploaded to Copr repository.
