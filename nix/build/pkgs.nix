# SPDX-FileCopyrightText: 2022 Oxhead Alpha
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ

{ sources ? import ../nix/sources.nix, pkgs ? import sources.nixpkgs { } }:
let
  ocaml-overlay = import ./ocaml-overlay.nix { inherit sources; };
  nixpkgs = import sources.nixpkgs { overlays = [ ocaml-overlay ]; };
in nixpkgs
