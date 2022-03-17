<!--
   - SPDX-FileCopyrightText: 2022 Oxhead Alpha
   - SPDX-License-Identifier: LicenseRef-MIT-OA
   -->

# Building and packaging tezos using nix

## Dynamically built binaries

In order to build all binaries run:
```bash
nix-build -A binaries
```

As an alternative you can build single binary:
```
nix-build -A binaries.tezos-client
```

This will produce `tezos-client` binary.
