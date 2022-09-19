# SPDX-FileCopyrightText: 2022 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

{ pkgs, meta, ...  }:
with pkgs; mkShell {
  buildInputs = [
    python3
    python3Packages.black
    shellcheck
    jq
    gh
    buildkite-agent
    wget
  ];
  OCTEZ_VERSION= with pkgs.lib; lists.last (strings.splitString "/" (meta.tezos_ref));
}
