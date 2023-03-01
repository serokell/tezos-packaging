<!--
   - SPDX-FileCopyrightText: 2022 Oxhead Alpha
   - SPDX-License-Identifier: LicenseRef-MIT-OA
   -->

# Setting up transaction rollup node on Ubuntu

At first you should originate rollup with the provided alias for some implicit account:
```
sudo -u tezos tezos-client originate tx rollup <ROLLUP_ALIAS> from <IMPLICIT_ACCOUNT_ALIAS>
```

After that, with the active `tezos-node` service available with the provided uri, run the following command
```
systemctl start tezos-tx-rollup-node-<proto>.service
```
Note: The `proto` variable can be every active protocol.

For futher details, see [the upstream documentation on transaction rollups](http://tezos.gitlab.io/active/transaction_rollups.html).

## Options and defaults

As any other `systemd` services ditributed here, rollup binaries have settable
options, see [the dedicated documentation](./configuration.md) to see their
default values and how to change these.
