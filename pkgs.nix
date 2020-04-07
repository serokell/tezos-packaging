# SPDX-FileCopyrightText: 2019 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: MPL-2.0

{ sources ? import ./nix/sources.nix, pkgs ? import sources.nixpkgs { } }:
let
  ocaml-overlay = import ./ocaml-overlay.nix { inherit sources pkgs; };
  static-overlay = import ./static-overlay.nix;
  normal = import sources.nixpkgs { overlays = [ ocaml-overlay ]; };
in normal // {
  pkgsMusl = (import sources.nixpkgs {
    overlays = [ ocaml-overlay static-overlay ];
  }).pkgsMusl;
}
