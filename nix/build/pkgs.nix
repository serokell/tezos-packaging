# SPDX-FileCopyrightText: 2019 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: MPL-2.0

{ sources ? import ../nix/sources.nix, pkgs ? import sources.nixpkgs { }, tezos-source ? null }:
let
  ocaml-overlay = import ./ocaml-overlay.nix { inherit sources pkgs tezos-source; };
  static-overlay = import ./static-overlay.nix;
  nixpkgs = import sources.nixpkgs { overlays = [ ocaml-overlay ]; };
in nixpkgs.extend (self: super: {
  pkgsMusl = super.pkgsMusl.extend static-overlay;
})
