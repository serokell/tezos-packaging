<!--
   - SPDX-FileCopyrightText: 2022 TQ Tezos <https://tqtezos.com/>
   -
   - SPDX-License-Identifier: LicenseRef-MIT-TQ
   -->

# Voting with voting wizard

This document explains how one can test voting via voting wizard on during all possible
amendment periods.

## Prerequisites

1) Install `tezos-baking` package should on your system.
2) Clone [local-chain repository](https://gitlab.com/morley-framework/local-chain).

## Test scenario workflow

1) Generate a pair of keys associated with `baker` alias:

```
sudo -u tezos tezos-client gen keys baker
```

2) In a separate terminal start a [voting scenario script](https://gitlab.com/morley-framework/local-chain#voting-scenario) from the local-chain repo.

This script will provide you a path to the node config that will be used by the custom baking service.

3) Provide address generated on the first step to the `voting.py` script. This address will receive some amount of XTZ.

4) Create a config for the custom baking service that will be used by the voting wizard:

```
sudo cp /etc/default/tezos-baking-custom@ /etc/default/tezos-baking-custom@voting
```
Edit with the config provided by the voting script on the second step:
```
DATA_DIR="/var/lib/tezos/.tezos-client"
NODE_RPC_ENDPOINT="http://localhost:8732"
BAKER_ADDRESS_ALIAS="baker"
CUSTOM_NODE_CONFIG="<paste your path to the node config here>"
RESET_ON_STOP=""
```

Additionally, you can set `RESET_ON_STOP="true"` to enable automatic node directory removal which will
be triggered once custom baking service will be stopped.

5) Start custom baking service:

```
sudo systemctl start tezos-baking-custom@voting
```

Note that `tezos-node` service may take some time to generate a fresh identity and start.

To check the status of the node service run:
```
systemctl status tezos-node-custom@voting
```

6) Register `baker` key as delegate once `tezos-node` is up and running:
```
sudo -u tezos tezos-client register key baker as delegate
```

7) After that `voting.py` will start going through the voting cycle.

The script will stop at the beginning of each voting period that requires voting and ask you to vote.

Launch `tezos-voting-wizard`, select `custom` network with `voting` name and submit your vote.
Under normal conditions, you won't have to adjust any information about your baking service.

Once you'll vote, you should prompt the `voting.py` script to continue going through the voting cycle.

8) Stop custom baking service once voting cycle is over:
```
sudo systemctl stop tezos-baking-custom@voting
```