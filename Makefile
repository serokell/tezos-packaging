# SPDX-FileCopyrightText: 2019 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: MPL-2.0
ts := $(shell date +"%Y%m%d%H%M")

.PHONY: binaries rpm-packages deb-packages

binaries:
		cp $(shell nix-build --tarball-ttl 100000000 -A binaries --no-out-link)/* ./

rpm-packages:
		nix-build --tarball-ttl 100000000 -A rpm -o rpm-packages --arg timestamp $(ts)

deb-packages:
		nix-build --tarball-ttl 100000000 -A deb -o deb-packages --arg timestamp $(ts)
