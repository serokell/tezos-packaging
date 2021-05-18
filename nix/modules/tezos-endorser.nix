# SPDX-FileCopyrightText: 2021 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ

{config, lib, pkgs, ...}:

with lib;

let
  tezos-endorser-pkgs = {
    "009-PsFLoren" =
      "${pkgs.ocamlPackages.tezos-baker-009-PsFLoren}/bin/tezos-baker-009-PsFLoren";
  };
  common = import ./common.nix { inherit lib; inherit pkgs; };
  cfg = config.services.tezos-endorser;
  instanceOptions = types.submodule ( {...} : {
    options = common.daemonOptions // {

      enable = mkEnableOption "Tezos endorser service";

      bakerAccountAlias = mkOption {
        type = types.str;
        default = "";
        description = ''
          Alias for the tezos-baker account.
        '';
      };

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
  config =
    let endorser-script = node-cfg: ''
        ${tezos-endorser-pkgs.${node-cfg.baseProtocol}} -d "$STATE_DIRECTORY/client/data" \
        -E "http://localhost:${toString node-cfg.rpcPort}" \
        run with local node "$STATE_DIRECTORY/node/data" ${node-cfg.bakerAccountAlias}
      '';
    in common.genDaemonConfig cfg.instances "endorser" tezos-endorser-pkgs endorser-script;
}
