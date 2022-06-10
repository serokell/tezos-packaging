# SPDX-FileCopyrightText: 2021 TQ Tezos <https://tqtezos.com/>
# SPDX-License-Identifier: LicenseRef-MIT-TQ

{ pkgs, ... }:
(pkgs.python3.buildEnv.override {
  extraLibs = with pkgs.python3Packages; [ pyyaml ];
}).env
