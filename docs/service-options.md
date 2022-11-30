<!--
   - SPDX-FileCopyrightText: 2022 Oxhead Alpha
   - SPDX-License-Identifier: LicenseRef-MIT-OA
   -->
# Systemd service options

The [`systemd` services](./systemd.md) provided by the packages here utilize
options to to define their behavior.

All these options are defined as environment variables and are located in files
in the `/etc/default` system directory.

## Changing options

Options can be modified by editing the configuration files.

For example, using the commonly pre-installed `nano` editor:
```sh
sudo nano /etc/default/tezos-node-mainnet
```
can be used to modify the behavior of the `mainnet` tezos node service (and not
only, see below).

Note that if a service is already running it will be necessary to restart it, e.g.
```sh
sudo systemctl restart tezos-node-mainnet.service
```
in order for the changes to take effect.

In case you [set up baking using the `tezos-setup`](./baking.md), running:
```sh
sudo systemctl restart tezos-baking-<network>.service
```
will be sufficient, as all the services involved will be restarted.
Running again `tezos-setup` and following the setup process is also an option.

## Utility node scripts

Installing packages on Ubuntu or Fedora will also install some utility scripts
for tezos nodes: a `tezos-node-<network>` for every currently supported Tezos `<network>`.

Calling these scripts has the same effect as running `tezos-node` with the env
variables in the `/etc/default/tezos-node-<network>` given to it.

## Available options

Below is a list of all the environment variables that can affect the services.

Note that, because they are inter-connected, some changes affect multiple services.
For example, it's sufficient to change the node data directory option in the `node`
configuration file and the appropriate `baker`s and `baking` services will be
aware of the change as well.


| Variable                       | Location                        | Description                                                                              | Potentially affected services                                                                |
| ------------------------------ | ------------------------------- | ---------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| `NODE_RPC_SCHEME`              | `tezos-accuser-<proto>`         | Scheme of the node RPC endpoint, e.g. `http`, `https`                                    | `tezos-accuser-<proto>`                                                                      |
| `NODE_RPC_ADDR`                | `tezos-accuser-<proto>`         | Address of the node RPC endpoint, e.g. `localhost:8732`, `node.example.org:8732`         | `tezos-accuser-<proto>`                                                                      |
| `TEZOS_CLIENT_DIR`             | `tezos-accuser-<proto>`         | Path to the tezos client data directory, e.g. `/var/lib/tezos/.tezos-client`             | `tezos-accuser-<proto>`                                                                      |
| `TEZOS_CLIENT_DIR`             | `tezos-baker-<proto>`           | Tezos client data directory, e.g. `/var/lib/tezos/.tezos-client`                         | `tezos-baker-<proto>`                                                                        |
| `BAKER_ADDRESS_ALIAS`          | `tezos-baker-<proto>`           | Alias of the address to be used for baking, e.g. `baker`                                 | `tezos-baker-<proto>`                                                                        |
| `LIQUIDITY_BAKING_TOGGLE_VOTE` | `tezos-baker-<proto>`           | Liquidity baking toggle vote to be cast while baking, e.g. `pass`, `on`, `off`           | `tezos-baker-<proto>`                                                                        |
| `TEZOS_NODE_DIR`               | `tezos-baker-<proto>`           | Path to the tezos node data directory, e.g. `/var/lib/tezos/node`                        | `tezos-baker-<proto>`                                                                        |
| `NODE_RPC_SCHEME`              | `tezos-baker-<proto>`           | Scheme of the node RPC endpoint, e.g. `http`, `https`                                    | `tezos-baker-<proto>`                                                                        |
| `NODE_RPC_ADDR`                | `tezos-baker-<proto>`           | Address of the node RPC endpoint, e.g. `localhost:8732`, `node.example.org:8732`         | `tezos-baker-<proto>`                                                                        |
| `TEZOS_CLIENT_DIR`             | `tezos-baking-custom@<network>` | Path to the tezos client data directory, e.g. `/var/lib/tezos/.tezos-client`             | `tezos-baking-custom@<network>`                                                              |
| `NODE_RPC_SCHEME`              | `tezos-baking-custom@<network>` | Scheme of the node RPC endpoint, e.g. `http`, `https`                                    | `tezos-baking-custom@<network>`                                                              |
| `BAKER_ADDRESS_ALIAS`          | `tezos-baking-custom@<network>` | Alias of the address to be used for baking, e.g. `baker`.                                | `tezos-baking-custom@<network>`                                                              |
| `LIQUIDITY_BAKING_TOGGLE_VOTE` | `tezos-baking-custom@<network>` | Liquidity baking toggle vote to be cast while baking, e.g. `pass`, `on`, `off`           | `tezos-baking-custom@<network>`                                                              |
| `TEZOS_CLIENT_DIR`             | `tezos-baking-<network>`        | Path to the tezos client data directory, e.g. `/var/lib/tezos/.tezos-client`             | `tezos-baking-<network>`, `tezos-accuser-<proto>@<network>`, `tezos-baker-<proto>@<network>` |
| `NODE_RPC_SCHEME`              | `tezos-baking-<network>`        | Scheme of the node RPC endpoint, e.g. `http`, `https`                                    | `tezos-baking-<network>`, `tezos-accuser-<proto>@<network>`, `tezos-baker-<proto>@<network>` |
| `BAKER_ADDRESS_ALIAS`          | `tezos-baking-<network>`        | Alias of the address to be used for baking, e.g. `baker`.                                | `tezos-baking-<network>`, `tezos-accuser-<proto>@<network>`, `tezos-baker-<proto>@<network>` |
| `LIQUIDITY_BAKING_TOGGLE_VOTE` | `tezos-baking-<network>`        | Liquidity baking toggle vote to be cast while baking, e.g. `pass`, `on`, `off`           | `tezos-baking-<network>`, `tezos-accuser-<proto>@<network>`, `tezos-baker-<proto>@<network>` |
| `NODE_RPC_ADDR`                | `tezos-node-<network>`          | Address used by this node to serve the RPC, e.g. `127.0.0.1:8732`                        | `tezos-node-<network>`, `tezos-baking-<network>`, `tezos-baker-<proto>@<network>`            |
| `CERT_PATH`                    | `tezos-node-<network>`          | Path to the TLS certificate, e.g. `/var/lib/tezos/.tls-certificate`                      | `tezos-node-<network>`, `tezos-baking-<network>`, `tezos-baker-<proto>@<network>`            |
| `KEY_PATH`                     | `tezos-node-<network>`          | Path to the TLS key, e.g. `/var/lib/tezos/.tls-key`                                      | `tezos-node-<network>`, `tezos-baking-<network>`, `tezos-baker-<proto>@<network>`            |
| `TEZOS_NODE_DIR`               | `tezos-node-<network>`          | Path to the tezos node data directory, e.g. `/var/lib/tezos/node`                        | `tezos-node-<network>`, `tezos-baking-<network>`, `tezos-baker-<proto>@<network>`            |
| `NETWORK`                      | `tezos-node-<network>`          | Name of the network that this node will run on, e.g. `mainnet`, `ghostnet`               | `tezos-node-<network>`, `tezos-baking-<network>`, `tezos-baker-<proto>@<network>`            |
| `NODE_RPC_ADDR`                | `tezos-node-custom@<network>`   | Address used by this node to serve the RPC, e.g. `127.0.0.1:8732`                        | `tezos-baking-custom@<network>`, `tezos-node-custom@<network>`                               |
| `CERT_PATH`                    | `tezos-node-custom@<network>`   | Path to the TLS certificate, e.g. `/var/lib/tezos/.tls-certificate`                      | `tezos-baking-custom@<network>`, `tezos-node-custom@<network>`                               |
| `KEY_PATH`                     | `tezos-node-custom@<network>`   | Path to the TLS key, e.g. `/var/lib/tezos/.tls-key`                                      | `tezos-baking-custom@<network>`, `tezos-node-custom@<network>`                               |
| `TEZOS_NODE_DIR`               | `tezos-node-custom@<network>`   | Path to the tezos node data directory, e.g. `/var/lib/tezos/node`                        | `tezos-baking-custom@<network>`, `tezos-node-custom@<network>`                               |
| `CUSTOM_NODE_CONFIG`           | `tezos-node-custom@<network>`   | Path to the custom configuration file used by this node, e.g. `/var/lib/tezos/node.json` | `tezos-baking-custom@<network>`, `tezos-node-custom@<network>`                               |
| `RESET_ON_STOP`                | `tezos-node-custom@<network>`   | Whether the node should be reset when the node service is stopped, e.g. `true`           | `tezos-baking-custom@<network>`, `tezos-node-custom@<network>`                               |
| `TEZOS_CLIENT_DIR`             | `tezos-signer-<mode>`           | Path to the tezos client data directory, e.g. `/var/lib/tezos/.tezos-client`             | `tezos-signer-<mode>`                                                                        |
| `PIDFILE`                      | `tezos-signer-<mode>`           | File in which to write the signer process id, e.g. `/var/lib/tezos/.signer-pid`          | `tezos-signer-<mode>`                                                                        |
| `MAGIC_BYTES`                  | `tezos-signer-<mode>`           | Values allowed for the magic bytes.                                                      | `tezos-signer-<mode>`                                                                        |
| `CHECK_HIGH_WATERMARK`         | `tezos-signer-<mode>`           | Whether to apply the high watermark restriction or not, e.g. `true`                      | `tezos-signer-<mode>`                                                                        |
| `CERT_PATH`                    | `tezos-signer-http`             | Path to the TLS certificate, e.g. `/var/lib/tezos/.tls-certificate`                      | `tezos-signer-http`                                                                          |
| `KEY_PATH`                     | `tezos-signer-http`             | Path to the TLS key, e.g. `/var/lib/tezos/.tls-key`                                      | `tezos-signer-http`                                                                          |
| `ADDRESS`                      | `tezos-signer-http`             | Listening address or hostname for the signer, e.g. `localhost`                           | `tezos-signer-http`                                                                          |
| `PORT`                         | `tezos-signer-http`             | Listening HTTP port for the signer, e.g. `6732`                                          | `tezos-signer-http`                                                                          |
| `CERT_PATH`                    | `tezos-signer-https`            | Path to the TLS certificate, e.g. `/var/lib/tezos/.tls-certificate`                      | `tezos-signer-https`                                                                         |
| `KEY_PATH`                     | `tezos-signer-https`            | Path to the TLS key, e.g. `/var/lib/tezos/.tls-key`                                      | `tezos-signer-https`                                                                         |
| `ADDRESS`                      | `tezos-signer-https`            | Listening address or hostname for the signer, e.g. `localhost`                           | `tezos-signer-https`                                                                         |
| `PORT`                         | `tezos-signer-https`            | Listening HTTPS port for the signer, e.g. `443`                                          | `tezos-signer-https`                                                                         |
| `ADDRESS`                      | `tezos-signer-tcp`              | Listening address or hostname for the signer, e.g. `localhost`                           | `tezos-signer-tcp`                                                                           |
| `PORT`                         | `tezos-signer-tcp`              | Listening TCP port for the signer, e.g. `7732`                                           | `tezos-signer-tcp`                                                                           |
| `TIMEOUT`                      | `tezos-signer-tcp`              | Timeout used by the signer to close client connections (in seconds), e.g. `8`            | `tezos-signer-tcp`                                                                           |
| `SOCKET`                       | `tezos-signer-unix`             | Path to the local socket file, e.g. `/var/lib/tezos/.tezos-signer/socket`                | `tezos-signer-unix`                                                                          |
| `TEZOS_CLIENT_DIR`             | `tezos-tx-rollup-node-<proto>`  | Path to the tezos client data directory, e.g. `/var/lib/tezos/.tezos-client`             | `tezos-tx-rollup-node-<proto>`                                                               |
| `NODE_RPC_SCHEME`              | `tezos-tx-rollup-node-<proto>`  | Scheme of the node RPC endpoint, e.g. `http`, `https`                                    | `tezos-tx-rollup-node-<proto>`                                                               |
| `NODE_RPC_ADDR`                | `tezos-tx-rollup-node-<proto>`  | Address of the node RPC endpoint, e.g. `localhost:8732`, `node.example.org:8732`         | `tezos-tx-rollup-node-<proto>`                                                               |
| `ROLLUP_NODE_RPC_ENDPOINT`     | `tezos-tx-rollup-node-<proto>`  | Address of this rollup node RPC endpoint, e.g. `127.0.0.1:8472`                          | `tezos-tx-rollup-node-<proto>`                                                               |
| `ROLLUP_MODE`                  | `tezos-tx-rollup-node-<proto>`  | Rollup mode used by this node, e.g. `accuser`, `observer`, `batcher`                     | `tezos-tx-rollup-node-<proto>`                                                               |
| `ROLLUP_ALIAS`                 | `tezos-tx-rollup-node-<proto>`  | Alias of the address to be used for rollup, e.g. `rollup`                                | `tezos-tx-rollup-node-<proto>`                                                               |
