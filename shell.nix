# SPDX-FileCopyrightText: 2022 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

{ pkgs, ...  }:
with pkgs; mkShell {
  buildInputs = [
    nix
    nodePackages.bash-language-server
    nodePackages.yaml-language-server
    nodePackages.vscode-langservers-extracted
    python3Packages.python-lsp-server
    python3Packages.black
    shellcheck
    vagrant
  ];
  TEZOS_VERSION="v13.1";
}
