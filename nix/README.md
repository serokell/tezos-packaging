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
