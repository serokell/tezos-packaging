# SPDX-FileCopyrightText: 2019 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: MPL-2.0
ts := $(shell date +"%Y%m%d%H%M")

.PHONY: binaries binaries-mainnet

binaries:
		cp $(shell nix-build -A babylonnet-binaries --no-out-link)/* ./

binaries-mainnet:
		cp $(shell nix-build -A mainnet-binaries --no-out-link)/* ./

rpm-packages:
		nix-build -A rpm-packages -o rpm-packages --arg timestamp $(ts)

deb-packages:
		nix-build -A deb-packages -o deb-packages --arg timestamp $(ts)
