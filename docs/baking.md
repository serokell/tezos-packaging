<!--
   - SPDX-FileCopyrightText: 2021 Oxhead Alpha
   - SPDX-License-Identifier: LicenseRef-MIT-OA
   -->
# Baking with tezos-packaging on Ubuntu and Raspberry Pi OS

[⏩ Quick Start](#quick-start)

Tezos-packaging provides an easy way to install and set up the infrastructure for
interacting with the Tezos blockchain.

This article provides a step-by-step guide for setting up a baking instance for
Tezos on Ubuntu or Raspberry Pi OS.

However, a CLI wizard utility is provided for an easy, interactive setup.
It is the recommended way at the moment to set up a baking instance.

## Prerequisites

### Raspberry Pi system

To bake on a Raspberry Pi you will need a device that has at least 4 GB of RAM
and an arm64 processor; for example a Raspberry Pi 4B.

You will also need to run the [64bit version of the Raspberry Pi OS](https://www.raspberrypi.com/software/operating-systems/#raspberry-pi-os-64-bit),
that you can use by following the [installation instructions](https://www.raspberrypi.com/documentation/computers/getting-started.html#installing-the-operating-system).

### Installation

In order to run a baking instance, you'll need the following Tezos binaries:
`tezos-client`, `tezos-node`, `tezos-baker-<proto>`.

The currently supported protocol is `PtLimaPt` (used on `limanet`, `ghostnet` and `mainnet`).
Also, note that the corresponding packages have protocol
suffix in lowercase, e.g. the list of available baker packages can be found
[here](https://launchpad.net/~serokell/+archive/ubuntu/tezos/+packages?field.name_filter=tezos-baker&field.status_filter=published).

The most convenient way to orchestrate all these binaries is to use the `tezos-baking`
package, which provides predefined services for running baking instances on different
networks.

This package also provides a `tezos-setup` CLI utility, designed to
query all necessary configuration options and use the answers to automatically set up
a baking instance.

#### Add repository

On Ubuntu:

```
# Add PPA with Tezos binaries
sudo add-apt-repository ppa:serokell/tezos
```

Alternatively, use packages with release-candidate Tezos binaries:
```
# Or use PPA with release-candidate Tezos binaries
sudo add-apt-repository ppa:serokell/tezos-rc
```

On Raspberry Pi OS:

```
# Install software properties commons
sudo apt-get install software-properties-common
# Add PPA with Tezos binaries
sudo add-apt-repository 'deb http://ppa.launchpad.net/serokell/tezos/ubuntu focal main'
sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys 37B8819B7D0D183812DCA9A8CE5A4D8933AE7CBB
```

#### Install packages

```
sudo apt-get update
sudo apt-get install tezos-baking
```

Packages for `tezos-node` and `tezos-baker-<proto>` provide
systemd units for running the corresponding binaries in the background, these units
are orchestrated by the `tezos-baking-<network>` units.

## Packages and protocols updates

In order to have a safe transition during a new protocol activation on mainnet,
it's required to run two sets of daemons: for the current and for the upcoming protocol.

`tezos-baking` package aims to provide such a setup. This package is updated some time before
the new protocol is activated (usually 1-2 weeks) to run daemons for two protocols. Once the new
protocol is activated, the `tezos-baking` package is updated again to stop running daemons for the old protocol.

## Using the wizard

If at this point you want to set up the baking instance, or just a node, using the wizard, run:

```
tezos-setup
```

This wizard closely follows this guide, so for most setups it won't be necessary to follow
the rest of this guide.

## Setting up baking service

By default `tezos-baking-<network>.service` will be using:
* `/var/lib/.tezos-client` as the `tezos-client` data directory
* `/var/lib/tezos/node-<network>` as the `tezos-node` data directory
* `http://localhost:8732` as the `tezos-node` RPC address.

## Bootstrapping the node

A fully-synced local `tezos-node` is required for running a baking instance.

By default, service with `tezos-node` will start to bootstrap from scratch,
which will take a significant amount of time.
In order to avoid this, we suggest bootstrapping from a snapshot instead.

Snapshots can be downloaded from the following websites:
* [XTZ-Shots](https://xtz-shots.io/)
* [Lambs on acid](https://lambsonacid.nl/)

Download the snapshot for the desired network. We recommend to use rolling snapshots. This is
the smallest and the fastest mode that is sufficient for baking (you can read more about other
`tezos-node` history modes [here](https://tezos.gitlab.io/user/history_modes.html#history-modes)).

All commands within the service are run under the `tezos` user.

The `tezos-node` package provides `tezos-node-<network>` aliases that are equivalent to
running `tezos-node` with [the service options](./service-options.md).

In order to import the snapshot, run the following command:
```
sudo -u tezos tezos-node-<network> snapshot import <path to the snapshot file>
```

## Setting up baker key

Note that account activation from JSON file and baker registering require
running a fully-bootstrapped `tezos-node`. In order to start node service do the following:
```
sudo systemctl start tezos-node-<network>.service
```

Even after the snapshot import the node can still be out of sync and may require
some additional time to completely bootstrap.

In order to check whether the node is bootstrapped and wait in case it isn't,
you can use `tezos-client`:
```
sudo -u tezos tezos-client bootstrapped
```

By default `tezos-baking-<network>.service` will use the `baker` alias for the
key that will be used for baking and endorsing.

### Setting the Liquidity Baking toggle vote option

Since `PtJakart`, the `--liquidity-baking-toggle-vote` command line option for
`tezos-baker` is now mandatory. In our systemd services, it is set to `pass` by
default.
You can change it as desired in [the service config file](./service-options.md).

You can also use the [Setup Wizard](#using-the-wizard) which will handle everything for you.

<a name="import"></a>
### Importing the baker key

Import your baker secret key to the data directory. There are multiple ways to import
the key:

1) The secret key is stored on a ledger.

Open the Tezos Baking app on your ledger and run the following
to import the key:
```
sudo -u tezos tezos-client import secret key baker <ledger-url>
```
Apart from importing the key, you'll also need to set it up for baking. Open the Tezos
Baking app on your ledger and run the following:
```
sudo -u tezos tezos-client setup ledger to bake for baker
```

2) You know either the unencrypted or password-encrypted secret key for your address.

In order to import such a key, run:
```
sudo -u tezos tezos-client import secret key baker <secret-key>
```

1) Alternatively, you can generate a fresh baker key and fill it using faucet from https://teztnets.xyz.

In order to generate a fresh key run:
```
sudo -u tezos tezos-client gen keys baker
```
The newly generated address will be displayed as a part of the command output.

Then visit https://teztnets.xyz and fill the address with at least 6000 XTZ on the desired testnet.

<a name="registration"></a>
### Registering the baker
Once the key is imported, you'll need to register your baker. If you imported your key
using a ledger, open a Tezos Wallet or Tezos Baking app on your ledger again. In any
case, run the following command:
```
sudo -u tezos tezos-client register key baker as delegate
```

Check a blockchain explorer (e.g. https://tzkt.io/ or https://tzstats.com/) to see the baker status and
baking rights of your account.

## Starting baking instance

Once the key is imported and the baker registered, you can start your baking instance:
```
sudo systemctl start tezos-baking-<network>.service
```

This service will trigger the following services to start:
* `tezos-node-<network>.service`
* `tezos-baker-<proto>@<network>.service`

Once services have started, you can check their logs via `journalctl`:
```
journalctl -f _UID=$(id tezos -u)
```
This command will show logs for all services that are using the `tezos` user.

You'll see the following messages in the logs in case everything has started
successfully:
```
Baker started.
```

To stop the baking instance run:
```
sudo systemctl stop tezos-baking-<network>.service
```

## Advanced baking instance setup

These services have several options that can be modified to change their behavior.
See [the dedicated documentation](./service-options.md) for more information on
how to do that.

### Using a custom chain

In case you want to set up a baking instance on a custom chain instead of relying on mainnet
or official testnets, you can do so:

1. Create a config file for future custom baking instance:
  ```bash
  sudo cp /etc/default/tezos-baking-custom@ /etc/default/tezos-baking-custom@<chain-name>
  ```
2. [Edit the `tezos-baking-custom@<chain-name>` configuration](./service-options.md)
 and set the `CUSTOM_NODE_CONFIG` variable to the path to your config file.
3. Start custom baking service:
  ```bash
  sudo systemctl start tezos-baking-custom@<chain-name>
  ```
4. Check that all parts are indeed running:
  ```bash
  systemctl status tezos-node-custom@<chain-name>
  systemctl status tezos-baker-ptkathma@custom@<chain-name>.service
```

If at any point after that you want to reset the custom baking service, you can set
`RESET_ON_STOP` to `true` [in the `tezos-baking-custom@<chain-name>` configuration](./service-options.md) and run:

```bash
sudo systemctl stop tezos-baking-custom@voting
```

Manually resetting is possible through:

1. Removing the custom chain node directory, `/var/lib/tezos/node-custom@<chain-name>` by default.
2. Deleting `blocks`, `nonces`, and `endorsements` from the `tezos-client` data directory,
  `/var/lib/tezos/.tezos-client` by default.

## Quick Start

<details>
 <summary>
   <em>Optional</em> Create new Ubuntu virtual machine...
 </summary>

A quick way to spin up a fresh Ubuntu virtual machine is
to use [Multipass](https://multipass.run/) (reduce disk if this is
to be used with a test network or a mainnet node in rolling history mode):

```
multipass launch --cpus 2 --disk 100G --mem 4G --name tezos
```

and then log in:

```
multipass shell tezos
```

> Note that on Windows and MacOS this VM will not have access to USB and
> thus is not suitable for using with Ledger Nano S.

</details>

1) Install `tezos-baking` package following [these instructions](#add-repository).

2) Run `tezos-setup` and follow the instructions there.

<details>
 <summary>
  <em>Optional</em> Allow RPC access from virtual machine's host...
 </summary>

[Update the `tezos-node-<network>` service configuration](./service-options.md)
and set the `NODE_RPC_ADDR` to `0.0.0.0:8732`.

Then restart the service:
```
sudo systemctl restart tezos-node-<network>
```

</details>
