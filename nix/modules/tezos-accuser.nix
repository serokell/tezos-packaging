# SPDX-FileCopyrightText: 2021 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

{config, lib, pkgs, ...}:

with lib;

let
  octez-accuser-pkgs = {
    "PtLimaPt" =
      "${pkgs.octezPackages.octez-accuser-PtLimaPt}/bin/octez-accuser-PtLimaPt";
  };
  cfg = config.services.octez-accuser;
  common = import ./common.nix { inherit lib; inherit pkgs; };
  instanceOptions = types.submodule ( {...} : {
    options = common.daemonOptions // {

      enable = mkEnableOption "Octez accuser service";

    };
  });

in {
  options.services.octez-accuser = {
    instances = mkOption {
      type = types.attrsOf instanceOptions;
      description = "Configuration options";
      default = {};
    };
  };
  config =
    let accuser-start-script = node-cfg: concatMapStringsSep "\n" (baseProtocol:
      ''
        ${octez-accuser-pkgs.${baseProtocol}} -d "$STATE_DIRECTORY/client/data" \
        -E "http://localhost:${toString node-cfg.rpcPort}" \
        run "$@" &
      '') node-cfg.baseProtocols;
    in common.genDaemonConfig {
      instancesCfg = cfg.instances;
      service-name = "accuser";
      service-pkgs = octez-accuser-pkgs;
      service-start-script = accuser-start-script;
    };
}
