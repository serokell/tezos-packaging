<!--
   - SPDX-FileCopyrightText: 2022 Oxhead Alpha
   - SPDX-License-Identifier: LicenseRef-MIT-OA
   -->

# Building and packaging tezos using nix

## Dynamically built binaries

In order to build all binaries run at the root of project:
```bash
nix build .
```

As an alternative you can build single binary:
```
nix build .#tezos-client
```

This will produce `tezos-client` binary.
