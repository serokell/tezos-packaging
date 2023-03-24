<!--
   - SPDX-FileCopyrightText: 2021 Oxhead Alpha
   - SPDX-License-Identifier: LicenseRef-MIT-OA
   -->
# Brew tap for macOS

If you're using macOS and `brew`, you can install Octez binaries from the taps provided
by this repository. There are two taps: one for the latest stable release of Octez and
one for the latest release candidate of Octez.

In order to use latest stable version run the following:
```
brew tap serokell/tezos-packaging-stable https://github.com/serokell/tezos-packaging-stable.git
```

In order to use the latest release candidate version run the following:
```
brew tap serokell/tezos-packaging-rc https://github.com/serokell/tezos-packaging-rc.git
```

Once the desired tap is selected, you can install the chosen package, e.g.:
```
brew install tezos-client
```

For faster formulae installation we provide prebuilt bottles for some macOS versions
in our releases, see [our support policy](./support-policy.md#macos-brew-formulae)
for more information.

## Launchd background services on macOS.

IMPORTANT: All provided `launchd` services are run as a user agents, thus they're stopped after the logout.

`tezos-accuser-<proto>`, `tezos-baker-<proto>` formulas
provide backround services for running the corresponding daemons.

Since `tezos-node` and `tezos-signer` need multiple services they are provided
in dedicated meta-formulas. These formulas don't install any binaries and only add
background services.

Formulae with `tezos-node` background services are, for example:
* `tezos-node-mainnet`
* `tezos-node-ghostnet`

The formulae with `tezos-signer` background services are instead:
* `tezos-signer-http`
* `tezos-signer-https`
* `tesos-signer-tcp`
* `tezos-signer-unix`

To start the service: `brew services start <formula>`.

To stop the service: `brew services stop <formula>`.

All of the brew services have various configurable env variables. These variables
can be changed in the corresponding `/usr/local/Cellar/tezos-signer-tcp/<version>/homebrew.mxcl.<formula>.plist`.
Once the configuration is updated, you should restart the service:
`brew services restart <formula>`.

## Building brew bottles

In order to build bottles with Tezos binaries run the [`build-one-bottle.sh`](../scripts/build-one-bottle.sh)
script with the formula that you want to build. For example:
```
./scripts/build-one-bottle.sh tezos-client
```

Note that several formulae have `tezos-sapling-params` has a dependency, so you
might need to run:
```
brew install --formula ./Formula/tezos-sapling-params.rb
```
first.

Building many of these might take a while, because builds don't share common parts
and for each binary the dependencies are compiled from scratch.
Once the bottles are built, the corresponding sections in the formulae should be updated.
Also, bottles should be uploaded to the release artifacts.
