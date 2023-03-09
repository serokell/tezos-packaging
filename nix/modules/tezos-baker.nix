# SPDX-FileCopyrightText: 2021 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

{config, lib, pkgs, ...}:

with lib;

let
  octez-baker-pkgs = {
    "PtLimaPt" =
      "${pkgs.octezPackages.octez-baker-PtLimaPt}/bin/octez-baker-PtLimaPt";
  };
  octez-client = "${pkgs.octezPackages.octez-client}/bin/octez-client";
  cfg = config.services.octez-baker;
  common = import ./common.nix { inherit lib; inherit pkgs; };
  instanceOptions = types.submodule ( {...} : {
    options = common.daemonOptions // {

      enable = mkEnableOption "Octez baker service";

      bakerSecretKey = mkOption {
        type = types.nullOr types.str;
        default = null;
        description = ''
          If provided, secret key will be imported for 'bakerAccountAlias' before
          starting the baker daemon.
        '';
      };

      bakerAccountAlias = mkOption {
        type = types.str;
        default = "";
        description = ''
          Alias for the octez-baker account.
        '';
      };

      liquidityBakingToggleVote = mkOption {
        type = types.enum [ "on" "of" "pass" ];
        default = "pass";
        description = ''
          Vote to continue (option 'on') or end (option 'off') the liquidity
          baking subsidy. Or choose to pass (option 'pass')
        '';
      };

    };
  });

in {
  options.services.octez-baker = {
    instances = mkOption {
      type = types.attrsOf instanceOptions;
      description = "Configuration options";
      default = {};
    };
  };
  config =
    let baker-start-script = node-cfg:
      let
        voting-option = "--liquidity-baking-toggle-vote ${node-cfg.liquidityBakingToggleVote}";
      in concatMapStringsSep "\n" (baseProtocol:
      ''
        ${octez-baker-pkgs.${baseProtocol}} -d "$STATE_DIRECTORY/client/data" \
        -E "http://localhost:${toString node-cfg.rpcPort}" \
        run with local node "$STATE_DIRECTORY/node/data" ${voting-option} ${node-cfg.bakerAccountAlias} &
      '') node-cfg.baseProtocols;
        baker-prestart-script = node-cfg: if node-cfg.bakerSecretKey != null then ''
          ${octez-client} -d "$STATE_DIRECTORY/client/data" import secret key "${node-cfg.bakerAccountAlias}" ${node-cfg.bakerSecretKey} --force
          '' else "";
    in common.genDaemonConfig {
      instancesCfg = cfg.instances;
      service-name = "baker";
      service-pkgs = octez-baker-pkgs;
      service-start-script = baker-start-script;
      service-prestart-script = baker-prestart-script;
    };
}
