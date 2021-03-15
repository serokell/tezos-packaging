# SPDX-FileCopyrightText: 2021 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ

{config, lib, pkgs, ...}:

with lib;

let
  tezos-endorser-pkgs = {
    "007-PsDELPH1" =
      "${pkgs.ocamlPackages.tezos-endorser-007-PsDELPH1}/bin/tezos-endorser-007-PsDELPH1";
    "008-PtEdo2Zk" =
      "${pkgs.ocamlPackages.tezos-endorser-008-PtEdo2Zk}/bin/tezos-endorser-008-PtEdo2Zk";
    "009-PsFLoren" =
      "${pkgs.ocamlPackages.tezos-baker-009-PsFLoren}/bin/tezos-baker-009-PsFLoren";
  };
  common = import ./common.nix { inherit lib; };
  cfg = config.services.tezos-endorser;
  instanceOptions = types.submodule ( {...} : {
    options = common.daemonOptions // {

      enable = mkEnableOption "Tezos endorser service";

    };
  });

in {
  options.services.tezos-endorser = {
    instances = mkOption {
      type = types.attrsOf instanceOptions;
      description = "Configuration options";
      default = {};
    };
  };
  config = common.genDaemonConfig cfg.instances "endorser" tezos-endorser-pkgs;
}
