<!--
   - SPDX-FileCopyrightText: 2022 Oxhead Alpha
   - SPDX-License-Identifier: LicenseRef-MIT-OA
   -->

# Building and packaging tezos using nix

**⚠️ Deprecation Warning:** *Nix build is deprecated.*

## Dynamically built binaries

In order to build all binaries run at the root of this project:
```bash
nix build .
```

Alternatively, you can build a single binary too.
For example, this:
```
nix build .#tezos-client
```
will produce the `tezos-client` binary.
