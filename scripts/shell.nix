# SPDX-FileCopyrightText: 2021 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

{ pkgs ? import (import ../nix/nix/sources.nix {}).nixpkgs { } }:
with pkgs;
mkShell {
  buildInputs = [
    coreutils gnused gh git rename gnupg dput rpm debian-devscripts which util-linux perl
    jq niv
  ];
}
