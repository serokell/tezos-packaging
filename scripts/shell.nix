# SPDX-FileCopyrightText: 2019-2020 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: MPL-2.0

{ pkgs ? import (import ../nix/nix/sources.nix {}).nixpkgs {} }:
with pkgs;
mkShell {
  buildInputs = [ gitAndTools.hub git rename ];
}
