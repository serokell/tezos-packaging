# SPDX-FileCopyrightText: 2021 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

{config, lib, pkgs, ...}:

with lib;

let
  tezos-baker-pkgs = {
    "011-PtHangz2" =
      "${pkgs.ocamlPackages.tezos-baker-011-PtHangz2}/bin/tezos-baker-011-PtHangz2";
    "012-Psithaca" =
      "${pkgs.ocamlPackages.tezos-baker-012-Psithaca}/bin/tezos-baker-012-Psithaca";
  };
  cfg = config.services.tezos-baker;
  common = import ./common.nix { inherit lib; inherit pkgs; };
  instanceOptions = types.submodule ( {...} : {
    options = common.daemonOptions // {

      enable = mkEnableOption "Tezos baker service";

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
        run with local node "$STATE_DIRECTORY/node/data" ${node-cfg.bakerAccountAlias}
      '';
    in common.genDaemonConfig cfg.instances "baker" tezos-baker-pkgs baker-script;
}
