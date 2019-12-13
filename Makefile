# SPDX-FileCopyrightText: 2019 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: MPL-2.0
ts := $(shell date +"%Y%m%d%H%M")

binaries:
		nix-build -A babylonnet-binaries -o binaries
		cp binaries/* ./
		rm binaries

binaries-mainnet:
		nix-build -A mainnet-binaries -o binaries
		cp binaries/* ./
		rm binaries

rpm-packages:
		nix-build -A rpm-packages -o rpm-packages --arg timestamp $(ts)

deb-packages:
		nix-build -A deb-packages -o deb-packages --arg timestamp $(ts)
