# SPDX-FileCopyrightText: 2019 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ

{ sources ? import ../nix/sources.nix, pkgs ? import sources.nixpkgs { } }:
let
  ocaml-overlay = import ./ocaml-overlay.nix { inherit sources pkgs; };
  static-overlay = import ./static-overlay.nix;
  nixpkgs = import sources.nixpkgs { overlays = [ ocaml-overlay ]; };
in nixpkgs.extend (self: super: {
  pkgsMusl = super.pkgsMusl.extend static-overlay;
})
