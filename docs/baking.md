<!--
   - SPDX-FileCopyrightText: 2021 TQ Tezos <https://tqtezos.com/>
   -
   - SPDX-License-Identifier: LicenseRef-MIT-TQ
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

You will also need to run the 64bit version of the [Raspberry Pi OS](https://www.raspberrypi.org/software/),
that you can use by following the [installation instructions](https://www.raspberrypi.org/documentation/installation/installing-images/)
with an image downloaded from the [official 64bit repository](https://downloads.raspberrypi.org/raspios_arm64/images/).

### Installation

In order to run a baking instance, you'll need the following Tezos binaries:
`tezos-client`, `tezos-node`, `tezos-baker-<proto>`, `tezos-endorser-<proto>`.

The currently supported protocols are `009-PsFLoren` (used on `florencenet` and `mainnet`)
and `010-PtGRANAD` (used on `granadanet`).
Also, note that the corresponding packages have protocol
suffix in lowercase, e.g. the list of available baker packages can be found
[here](https://launchpad.net/~serokell/+archive/ubuntu/tezos/+packages?field.name_filter=tezos-baker&field.status_filter=published).

The most convenient way to orchestrate all these binaries is to use the `tezos-baking`
package, which provides predefined services for running baking instances on different
networks.

This package also provides a `tezos-setup-wizard` CLI utility, designed to
query all necessary configuration options and use the answers to automatically set up
a baking instance.

#### Add repository

On Ubuntu:

```
# Add PPA with Tezos binaries
sudo add-apt-repository ppa:serokell/tezos
```

On Raspberry Pi OS:

```
# Install software properties commons
sudo apt-get install software-properties-common
# Add PPA with Tezos binaries
sudo add-apt-repository 'deb http://ppa.launchpad.net/serokell/tezos/ubuntu bionic main'
sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys 37B8819B7D0D183812DCA9A8CE5A4D8933AE7CBB
```

#### Install packages

```
sudo apt-get update
sudo apt-get install tezos-baking
```

Packages for `tezos-node`, `tezos-baker-<proto>` and `tezos-endorser-<proto>` provide
systemd units for running the corresponding binaries in the background, these units
are orchestrated by the `tezos-baking-<network>` units.

## Using the wizard

If at this point you want to set up the baking instance, or just a node, using the wizard, run:

```
tezos-setup-wizard
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
* [Tezos Giganode Snapshots](https://snapshots-tezos.giganode.io/)
* [XTZ-Shots](https://xtz-shots.io/)

Download the snapshot for the desired network. We recommend to use rolling snapshots. This is
the smallest and the fastest mode that is sufficient for baking (you can read more about other
`tezos-node` history modes [here](https://tezos.gitlab.io/user/history_modes.html#history-modes)).

All commands within the service are run under the `tezos` user.

The `tezos-node` package provides `tezos-node-<network>` aliases that are equivalent to
`tezos-node --data-dir <DATA_DIR from the tezos-node-<network>.service>`.
These aliases can be used instead of providing `--data-dir` option to the `tezos-node`
invocations manually.

In order to import the snapshot, run the following command:
```
sudo -u tezos tezos-node-<network> snapshot import <path to the snapshot file>
```

## Setting up baker and endorser key

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

3) You have a faucet JSON file from https://faucet.tzalpha.net/.

In order to activate the account run:
```
sudo -u tezos tezos-client activate account baker with <path-to-downloaded-json>
```

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
* `tezos-endorser-<proto>@network.service`

Once services have started, you can check their logs via `journalctl`:
```
journalctl -f _UID=$(id tezos -u)
```
This command will show logs for all services that are using the `tezos` user.

You'll see the following messages in the logs in case everything has started
successfully:
```
Baker started.

Endorser started.
```

To stop the baking instance run:
```
sudo systemctl stop tezos-baking-<network>.service
```

## Advanced baking instance setup

### Using different data directories and node RPC address

In case you want to use a different `tezos-client` data directory or RPC address,
you should edit the `/etc/default/tezos-baking-<network>` file, e.g.:
```
sudo vim /etc/default/tezos-baking-<network>
```

In case you want to use a different `tezos-node` data directory, you
should instead edit the service configuration, using:
```
sudo systemctl edit --full tezos-node-<network>.service
```

### Using different account alias for baking

In case you want to use a different alias for the baking account:
1. replace `baker` with he desired alias in the sections about [importing](#import)
    and [registering](#registration) the baker key.
2. update the `BAKER_ADDRESS_ALIAS` by editing the
    `/etc/default/tezos-baking-<network>` file.

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

2) Run `tezos-setup-wizard` and follow the instructions there.

<details>
 <summary>
  <em>Optional</em> Allow RPC access from virtual machine's host...
 </summary>

Update service configuration:

```
sudo systemctl edit tezos-node-$tznet
```

An editor will open with service override configuration file.
Add the following:

```
[Service]
Environment="NODE_RPC_ADDR=0.0.0.0:8732"
```

Save and close the editor, restart the service:

```
sudo systemctl restart tezos-node-$tznet
```

</details>
