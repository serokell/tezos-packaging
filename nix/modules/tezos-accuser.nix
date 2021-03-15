# SPDX-FileCopyrightText: 2021 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ

{config, lib, pkgs, ...}:

with lib;

let
  tezos-accuser-pkgs = {
    "007-PsDELPH1" =
      "${pkgs.ocamlPackages.tezos-accuser-007-PsDELPH1}/bin/tezos-accuser-007-PsDELPH1";
    "008-PtEdo2Zk" =
      "${pkgs.ocamlPackages.tezos-accuser-008-PtEdo2Zk}/bin/tezos-accuser-008-PtEdo2Zk";
    "009-PsFLoren" =
      "${pkgs.ocamlPackages.tezos-baker-009-PsFLoren}/bin/tezos-baker-009-PsFLoren";
  };
  cfg = config.services.tezos-accuser;
  common = import ./common.nix { inherit lib; };
  instanceOptions = types.submodule ( {...} : {
    options = common.daemonOptions // {

      enable = mkEnableOption "Tezos accuser service";

    };
  });

in {
  options.services.tezos-accuser = {
    instances = mkOption {
      type = types.attrsOf instanceOptions;
      description = "Configuration options";
      default = {};
    };
  };
  config = common.genDaemonConfig cfg.instances "accuser" tezos-accuser-pkgs;
}
