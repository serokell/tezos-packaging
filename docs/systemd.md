<!--
   - SPDX-FileCopyrightText: 2021 Oxhead Alpha
   - SPDX-License-Identifier: LicenseRef-MIT-OA
   -->
# Systemd units with Tezos binaries

<a name="ubuntu-and-fedora"></a>
## Systemd units on Ubuntu and Fedora

`tezos-node`, `tezos-accuser-<proto>`, `tezos-baker-<proto>`,
and `tezos-signer` packages have systemd files included to the
Ubuntu and Fedora packages.

Once you've installed one of these packages, you can run the service
using the following command:
```
systemctl start <package-name>.service
```
To stop the service run:
```
systemctl stop <package-name>.service
```

Each service has its configuration file located in `/etc/default`.
These can be edited to modify the options and behavior of the services, see
[the dedicated documentation](./configuration.md) for more information.

Files created by the services will be located in `/var/lib/tezos/` by default.

<a name="generic-linux"></a>
## Systemd units on other Linux systems

If you're not using Ubuntu or Fedora you can still construct systemd units for
binaries from scratch.

For this you'll need a `.service` file to define each systemd service.
The easiest way to get one is to generate one with `docker` by running [`gen_systemd_service_file.py`](../gen_systemd_service_file.py).

First you'll need to set the `OCTEZ_VERSION` env variable, e.g.:
```sh
export OCTEZ_VERSION="v14.1"
```
Then you can use the script, specifying the binary name as an argument, e.g.:
```
./gen_systemd_service_file.py tezos-node
# or
./gen_systemd_service_file.py tezos-baker-PtLimaPt
```
After that you'll have `.service` files in the current directory.

Apart from these `.service` files you'll need the services' startup scripts and
default configuration files, they can be found in the
[`scripts`](../docker/package/scripts) and [`defaults`](../docker/package/defaults)
folders respectively.
Note: some of the default values are not in those files, as they are generated
dinamically, you can find the remaining options needed in
[the dedicated document](./configuration.md).

## Multiple similar systemd services

It's possible to run multiple similar services, e.g. two `tezos-node`s that run different
networks.

`tezos-node` packages provide multiple services out of the box:
- `tezos-node-mumbainet`
- `tezos-node-limanet`
- `tezos-node-ghostnet`
- `tezos-node-mainnet`

which run on the respective networks.

In order to start it run:
```
systemctl start tezos-node-<network>
```

Also, there are `tezos-node-<network>` binary aliases that are equivalent to
running `tezos-node` with [the service options](./configuration.md) given.

In addition to node services where the config is predefined to a specific network
(e.g. `tezos-node-mainnet` or `tezos-node-limanet`), it's possible to run
`tezos-node-custom` service.

Another case for running multiple similar systemd services is when one wants to have
multiple daemons that target different protocols.
Since daemons for different protocols are provided in the different packages, they will
have different service files. The only thing that needs to be changed is [the config file](./configuration.md).
One should provide desired node address, data directory for daemon files and node directory
(however, this is the case only for baker daemon).

`tezos-signer` package provides four services one for each mode in which signing daemon can run:
* Over TCP socket (`tezos-signer-tcp.service`).
* Over UNIX socker (`tezos-signer-unix.service`).
* Over HTTP (`tezos-signer-http.service`).
* Over HTTPS (`tezos-signer-https.service`)
Each signer service has [dedicated config files](./configuration.md) as well.
