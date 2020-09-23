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
