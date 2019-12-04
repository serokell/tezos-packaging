# SPDX-FileCopyrightText: 2019 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: MPL-2.0
ts := $(shell date +"%Y%m%d%H%M")

binary:
		nix-build -A tezos-client-babylonnet -o tezos-client
		cp tezos-client/tezos-client-babylonnet-* tezos-client-babylonnet
		rm tezos-client

binary-mainnet:
		nix-build -A tezos-client-mainnet -o tezos-client
		cp tezos-client/tezos-client-mainnet-* ./tezos-client-mainnet
		rm tezos-client

rpm:
		nix-build -A babylonnet-rpm-package -o tezos-client-package --arg timestamp $(ts)
		cp -a tezos-client-package/*.rpm .
		rm tezos-client-package

rpm-mainnet:
		nix-build -A mainnet-rpm-package -o tezos-client-package --arg timestamp $(ts)
		cp -a tezos-client-package/*.rpm .
		rm tezos-client-package

deb:
		nix-build -A babylonnet-deb-package -o tezos-client-package --arg timestamp $(ts)
		cp -a tezos-client-package/*.deb .
		rm tezos-client-package

deb-mainnet:
		nix-build -A mainnet-deb-package -o tezos-client-package --arg timestamp $(ts)
		cp -a tezos-client-package/*.deb .
		rm tezos-client-package

