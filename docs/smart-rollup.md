<!--
   - SPDX-FileCopyrightText: 2022 Oxhead Alpha
   - SPDX-License-Identifier: LicenseRef-MIT-OA
   -->

# Setting up smart rollup node on Ubuntu

At first you should originate rollup with the provided alias for some implicit account:
```
sudo -u tezos tezos-client originate smart rollup <ROLLUP_ALIAS> from <IMPLICIT_ACCOUNT_ALIAS> of kind <SMART_ROLLUP_KIND> of type <ROLLUP_PARAMETER_TYPE> with kernel <KERNEL>
```
Here:
* `ROLLUP_ALIAS` - Name for a new smart rollup
* `IMPLICIT_ACCOUNT_ALIAS` - Name of the account originating smart rollup
* `SMART_ROLLUP_KIND` - Kind of proof-generating virtual machine (PVM)
* `ROLLUP_PARAMETER_TYPE` - The interface of smart rollup (with entrypoints and signatures)
* `KERNEL` - The kernel of smart rollup that PVM can interpret

For more information on smart rollup origination, please check [official documentation](https://tezos.gitlab.io/alpha/smart_rollups.html#origination).

You can use the following command this way:

```
octez-client originate smart rollup "my-rollup" \
  from "bob" \
  of kind wasm_2_0_0 \
  of type unit \
  with kernel "file:kernel.hex"
```

For more extended step-by-step example, please proceed to this [tutorial](https://www.marigold.dev/post/originating-a-smart-rollup).

After that, with the active `tezos-node` service available with the provided uri, run the following command
```
systemctl start tezos-smart-rollup-node.service
```

For further details, see [the upstream documentation on smart rollups](http://tezos.gitlab.io/active/smart_rollups.html).

## Options and defaults

As any other `systemd` services ditributed here, rollup binaries have settable
options, see [the dedicated documentation](./configuration.md) to see their
default values and how to change these.
