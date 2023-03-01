<!--
   - SPDX-FileCopyrightText: 2022 Oxhead Alpha
   - SPDX-License-Identifier: LicenseRef-MIT-OA
   -->

# Voting with `tezos-packaging` on Ubuntu

`tezos-packaging` provides an easy way to propose amendments and cast votes on the Tezos blockchain.

This article documents the way to vote on Ubuntu, as well as any prerequisite steps necessary.

## Using the wizard

You can easily use the Tezos voting wizard to vote on mainnet.

A `mainnet` baking instance is recommended, but not necessary.
An easy way to configure one is with the Tezos Setup wizard, see the [baking](./baking.md#prerequisites) article for more details.
If a local baking setup is detected, the voting wizard will attempt to figure out
as many as the necessary info as possible from it.

With the [`tezos-baking`](./ubuntu.md/tezos-baking) package installed, launch the
interactive wizard with:
```bash
tezos-vote
```

The wizard displays the voting period and offers approppriate possible actions for that period.

# Advanced usage

## Using custom networks

`tezos-vote` supports voting on custom networks, in turn enabled by `tezos-packaging`'s
support for custom chain systemd services.
The process to set up a custom baking instance is documented [here](./baking.md#using-a-custom-chain).

After the custom baking instance is fully set up, you can vote or propose
amendments on it by running:

```bash
tezos-vote --network <custom-network-name>
```

E.g. if you have a custom baking instance `tezos-baking-custom@voting`, you can run:

```bash
tezos-vote --network voting
```

## Using testnets

`tezos-vote` also supports voting on currently running testnets, for example:

```bash
tezos-vote --network limanet
```
