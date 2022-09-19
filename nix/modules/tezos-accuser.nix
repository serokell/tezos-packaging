# SPDX-FileCopyrightText: 2021 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

{config, lib, pkgs, ...}:

with lib;

let
  tezos-accuser-pkgs = {
    "013-PtJakart" =
      "${pkgs.tezosPackages.tezos-accuser-013-PtJakart}/bin/tezos-accuser-013-PtJakart";
    "014-PtKathma" =
      "${pkgs.tezosPackages.tezos-accuser-014-PtKathma}/bin/tezos-accuser-014-PtKathma";
  };
  cfg = config.services.tezos-accuser;
  common = import ./common.nix { inherit lib; inherit pkgs; };
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
  config =
    let accuser-start-script = node-cfg: concatMapStringsSep "\n" (baseProtocol:
      ''
        ${tezos-accuser-pkgs.${baseProtocol}} -d "$STATE_DIRECTORY/client/data" \
        -E "http://localhost:${toString node-cfg.rpcPort}" \
        run "$@" &
      '') node-cfg.baseProtocols;
    in common.genDaemonConfig {
      instancesCfg = cfg.instances;
      service-name = "accuser";
      service-pkgs = tezos-accuser-pkgs;
      service-start-script = accuser-start-script;
    };
}
