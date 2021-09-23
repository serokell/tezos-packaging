# SPDX-FileCopyrightText: 2021 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ

{config, lib, pkgs, ...}:

with lib;

let
  tezos-endorser-pkgs = {
    "010-PtGRANAD" =
      "${pkgs.ocamlPackages.tezos-endorser-010-PtGRANAD}/bin/tezos-endorser-010-PtGRANAD";
    "011-PtHangzH" =
      "${pkgs.ocamlPackages.tezos-endorser-011-PtHangzH}/bin/tezos-endorser-011-PtHangzH";
  };
  common = import ./common.nix { inherit lib; inherit pkgs; };
  cfg = config.services.tezos-endorser;
  instanceOptions = types.submodule ( {...} : {
    options = common.daemonOptions // {

      enable = mkEnableOption "Tezos endorser service";

      endorserAccountAlias = mkOption {
        type = types.str;
        default = "";
        description = ''
          Alias for the tezos-endorser account.
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
        run ${node-cfg.endorserAccountAlias}
      '';
    in common.genDaemonConfig cfg.instances "endorser" tezos-endorser-pkgs endorser-script;
}
