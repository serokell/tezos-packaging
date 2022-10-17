<!--
   - SPDX-FileCopyrightText: 2022 Oxhead Alpha
   - SPDX-License-Identifier: LicenseRef-MIT-OA
   -->

# Setting up transaction rollup node on Ubuntu

`proto` variable can hold every active protocol, currently `PtKatham` and `PtLimaPt`.

By default, `tezos-tx-rollup-node-$proto.service` will use:
* `/var/lib/tezos/.tezos-client` as the `tezos-client` data directory, set in `DATA_DIR`
* `http://localhost:8732` as the `tezos-node` RPC address, set in `NODE_RPC_ENDPOINT`
* `127.0.0.1:8472` as the `tezos-tx-rollup-node-$proto` RPC address, set in `ROLLUP_NODE_RPC_ENDPOINT`
* `observer` as the `tezos-tx-rollup-node-$proto` working mode, set in `ROLLUP_MODE`
* `rollup` as the rollup alias, set in `ROLLUP_ALIAS`

At first you should originate rollup with the provided alias for some implicit account:
```
sudo -u tezos tezos-client originate tx rollup <ROLLUP_ALIAS> from <IMPLICIT_ACCOUNT_ALIAS>
```

After that, with the active `tezos-node` service available with the provided uri, run the following command
```
systemctl start tezos-tx-rollup-node-$proto.service
```

In order to change the defaults, open `/etc/default/tezos-tx-rollup-node-$proto` and modify the variables:

```
DATA_DIR="/var/lib/tezos/.tezos-client"
NODE_RPC_ENDPOINT="http://localhost:8732"
ROLLUP_NODE_RPC_ENDPOINT="127.0.0.1:8472"
ROLLUP_MODE="operator"
ROLLUP_ALIAS="custom-rollup"
```

Save and close the editor, restart the service:

```
sudo systemctl restart tezos-tx-rollup-node-$proto.service
```

For futher details, see [the documentation](http://tezos.gitlab.io/active/transaction_rollups.html).
