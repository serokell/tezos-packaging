# SPDX-FileCopyrightText: 2021 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ

{config, lib, pkgs, ...}:

with lib;

let
  tezos-baker-pkgs = {
    "007-PsDELPH1" =
      "${pkgs.ocamlPackages.tezos-baker-007-PsDELPH1}/bin/tezos-baker-007-PsDELPH1";
    "008-PtEdo2Zk" =
      "${pkgs.ocamlPackages.tezos-baker-008-PtEdo2Zk}/bin/tezos-baker-008-PtEdo2Zk";
    "009-PsFLoren" =
      "${pkgs.ocamlPackages.tezos-baker-009-PsFLoren}/bin/tezos-baker-009-PsFLoren";
  };
  cfg = config.services.tezos-baker;
  common = import ./common.nix { inherit lib; };
  instanceOptions = types.submodule ( {...} : {
    options = common.daemonOptions // {

      enable = mkEnableOption "Tezos baker service";

    };
  });

in {
  options.services.tezos-baker = {
    instances = mkOption {
      type = types.attrsOf instanceOptions;
      description = "Configuration options";
      default = {};
    };
  };
  config =
    let baker-script = node-cfg: ''
        ${tezos-baker-pkgs.${node-cfg.baseProtocol}} -d "$STATE_DIRECTORY/client/data" \
        -E "http://localhost:${toString node-cfg.rpcPort}" \
        run with local node "$STATE_DIRECTORY/node/data" "$@"
      '';
    in common.genDaemonConfig cfg.instances "baker" tezos-baker-pkgs baker-script;
}
