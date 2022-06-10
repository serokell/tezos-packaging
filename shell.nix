# SPDX-FileCopyrightText: 2022 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

{ pkgs, ...  }:
with pkgs; mkShell {
  buildInputs = [
    nix
    nodePackages.bash-language-server
    nodePackages.yaml-language-server
    nodePackages.vscode-json-languageserver
    python3Packages.python-lsp-server
    python3Packages.black
    shellcheck
  ];
  TEZOS_VERSION="v13.1";
}
