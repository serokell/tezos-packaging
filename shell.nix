# SPDX-FileCopyrightText: 2022 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

{ pkgs, meta, ...  }:
with pkgs; mkShell {
  buildInputs = [
    gh
    jq
    git
    rpm
    perl
    dput
    which
    gnupg
    rename
    gnused
    python3
    copr-cli
    coreutils
    util-linux
    shellcheck
    buildkite-agent
    debian-devscripts
    python3Packages.black
  ];
  OCTEZ_VERSION= with pkgs.lib; lists.last (strings.splitString "/" (meta.tezos_ref));
  DOCKER_BUILDKIT = 1;
}
