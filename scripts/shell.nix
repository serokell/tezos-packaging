# SPDX-FileCopyrightText: 2021 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

{ pkgs, ...}:
with pkgs;
mkShell {
  buildInputs = [
    # NOTE using the most recent nix for sticky nix flake lock update feature
    nix
    python3
    coreutils
    gnused
    gh
    git
    rename
    gnupg
    dput
    rpm
    debian-devscripts
    which
    util-linux
    perl
    jq
  ];
}
