<!--
   - SPDX-FileCopyrightText: 2021 TQ Tezos <https://tqtezos.com/>
   -
   - SPDX-License-Identifier: LicenseRef-MIT-TQ
   -->
# Baking with tezos-packaging on Ubuntu and Raspberry Pi OS

Tezos-packaging provides an easy way to install and set up the infrastructure for
interacting with the Tezos blockchain.

This article provides a step-by-step guide for setting up a baking instance for
Tezos on Ubuntu or Raspberry Pi OS.

## Prerequisites

### Raspberry Pi system

To bake on a Raspberry Pi you will need a device that has at least 4 GB of RAM
and an arm64 processor; for example a Raspberry Pi 4B.

You will also need to run the 64bit version of the [Raspberry Pi OS](https://www.raspberrypi.org/software/),
that you can use by following the [installation instructions](https://www.raspberrypi.org/documentation/installation/installing-images/)
with an image downloasd from the [official 64bit repository](https://downloads.raspberrypi.org/raspios_arm64/images/).

### Installing required packages

In order to run a baking instance, you'll need the following Tezos binaries:
`tezos-client`, `tezos-node`, `tezos-baker-<proto>`, `tezos-endorser-<proto>`.

The currently used proto is `008-PtEdo2Zk` (used on `mainnet` and `edo2net`).
Also, note that the corresponding packages have protocol
suffix in lowercase, e.g. the list of available baker packages can be found
[here](https://launchpad.net/~serokell/+archive/ubuntu/tezos/+packages?field.name_filter=tezos-baker&field.status_filter=published).

To install them, run the following commands:

#### On Ubuntu
```
# Add PPA with Tezos binaries
sudo add-apt-repository ppa:serokell/tezos
sudo apt-get update
# Install packages
sudo apt-get install tezos-client tezos-node tezos-baker-<proto> tezos-endorser-<proto>
```

#### On Raspberry Pi OS
```
# Intall software properties commons
sudo apt-get install software-properties-common
# Add PPA with Tezos binaries
sudo add-apt-repository 'deb http://ppa.launchpad.net/serokell/tezos/ubuntu bionic main'
sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys 37B8819B7D0D183812DCA9A8CE5A4D8933AE7CBB
sudo apt-get update
# Install packages
sudo apt-get install tezos-client tezos-node tezos-baker-<proto> tezos-endorser-<proto>
```

Packages for `tezos-node`, `tezos-baker-<proto>` and `tezos-endorser-<proto>` provide
systemd units for running the corresponding binaries in the background.

## Setting up the tezos-node

The easiest way to set up a node running on the `mainnet` or one of the
testnets (e.g. `edo2net`) is to use one of the predefined
`tezos-node-<network>.services` systemd services provided in the `tezos-node`
package.

However, by default, these services will start to bootstrap the node from scratch,
which will take a significant amount of time.
In order to avoid this, we suggest bootstrapping from a snapshot instead.

### Setting up node service

`tezos-node-<network>.service` has `/var/lib/tezos/node-<network>` as a data directory
and `http://localhost:8732` as its RPC address by default.

In case you want to use a different data directory or RPC address,
you should update the service configuration. To edit the service configuration, run:
```
sudo systemctl edit --full tezos-node-<network>.service
```

### Bootstrapping the node

In order to run a baker locally, you'll need a fully-synced local `tezos-node`.

The fastest way to bootstrap the node is to import a snapshot.
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

### Starting the node

After the snapshot import, you can finally start the node by running:
```
sudo systemctl start tezos-node-<network>.service
```

Note that even after the snapshot import the node can still be out of sync. It may require
some additional time to completely bootstrap. In order to check whether the node is bootstrapped,
you can use `tezos-client`:
```
sudo -u tezos tezos-client bootstrapped
```

To stop the node, run:
```
sudo systemctl stop tezos-node-<network>.service
```

If you want the service to start automatically at boot, use `enable`:
```
sudo systemctl enable tezos-node-edo2net.service
```
and to disable it from doing so, instead use:
```
sudo systemctl disable tezos-node-edo2net.service
```

You can check node logs via `journalctl`:
```
journalctl -u tezos-node-<network>.service
```

## Setting up baker and endorser daemons

### Setting up daemon data directories

Data directories for baker and endorser daemons are defined in the
`/etc/default/tezos-baker-<proto>` and `/etc/default/tezos-endorser-<proto>`.
By default, both these daemons have `/var/lib/tezos/.tezos-client` set as a `DATA_DIR`.

Additionally, you need to specify `NODE_DATA_DIR` in the `/etc/default/tezos-baker-<proto>`
to point at the desired node data directory, e.g. `/var/lib/tezos/node-<network>`.


### Importing the baker key

Import your baker secret key to the data directory. There are multiple ways to import
the key:

1) You have faucet JSON file from https://faucet.tzalpha.net/.

In order to activate account run:
```
sudo -u tezos tezos-client activate account <alias> <path-to-downloaded-json>
```

2) You know either the unencrypted or password-encrypted secret key for your address.

In order to import such a key, run:
```
sudo -u tezos tezos-client import secret key <alias> <secret-key>
```
3) The secret key is stored on a ledger.

Open the Tezoz Wallet app on your ledger and run the following
to import the key:
```
sudo -u tezos tezos-client import secret key <alias> <ledger-url>
```
Apart from importing the key, you'll also need to set it up for baking. Open Tezos Baking app
on your ledger and run the following:
```
sudo -u tezos tezos-client setup ledger to bake for <alias>
```

### Registering the baker
Once the key is imported, you'll need to register your baker, in order to do that run the following
command:
```
sudo -u tezos tezos-client register key <alias> as delegate
```

Check a blockchain explorer (e.g. https://tzkt.io/ or https://tzstats.com/) to see the baker status and
baking rights of your account.

### Updating baker and endorser daemons configuration
Apart from that, you'll need to update the `BAKER_ACCOUNT` and `ENDORSER_ACCOUNT` (in
`/etc/default/tezos-baker-<proto>` and `/etc/default/tezos-endorser-<proto>` respectively) in
accordance to the **alias** of the imported key.

### Starting daemons

Once the key is imported and the configs are updated, you can start the baker and endorser daemons:
```
sudo systemctl start tezos-baker-<proto>.service
sudo systemctl start tezos-endorser-<proto>.service
```

If the node isn't bootstrapped yet, the baker and endorser daemons will wait for it to bootstrap.

Note that if you're baking with the ledger key, you should have the Tezos Baking app open.

Once the services are started, you can check their logs via `journalctl`:
```
journalctl -u tezos-baker-<proto>.service
journalctl -u tezos-endorser-<proto>.service
```

If everything was set up correctly, you shouldn't see any errors in the logs.

Logs for successfully started baker service should begin with:
```
Node is bootstrapped.
Baker started.
```

Logs for successfully started endorser service should begin with:
```
Node is bootstrapped.
Endorser started.
```
