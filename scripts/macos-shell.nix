# SPDX-FileCopyrightText: 2022 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

# This shell is supposed to be used on macOS machines

{ pkgs ? import (import ../nix/nix/sources.nix {}).nixpkgs { } }:
with pkgs;
mkShell {
  buildInputs = [
    coreutils gnused gh git bash
  ];
}
