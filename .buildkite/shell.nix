# SPDX-FileCopyrightText: 2021 TQ Tezos <https://tqtezos.com/>
# SPDX-License-Identifier: LicenseRef-MIT-TQ

{ pkgs, ... }:
with pkgs; mkShell {
  buildInputs = [
    (python3.withPackages (ps: with ps; [ pyyaml ]))
    (writeShellScriptBin "copr-cli" ''/run/wrappers/bin/sudo -u copr-uploader /run/current-system/sw/bin/copr-cli "$@"'')
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
