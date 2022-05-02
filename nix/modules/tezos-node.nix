# SPDX-FileCopyrightText: 2021 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

{config, lib, pkgs, ...}:

with lib;

let
  tezos-node-pkg = pkgs.ocamlPackages.tezos-node;
  cfg = config.services.tezos-node;
  sources = import ../nix/sources.nix;
  genConfigCommand = historyMode: rpcPort: netPort: network: options: ''
    --data-dir "$node_data_dir" \
    --history-mode "${historyMode}" \
    --rpc-addr ":${toString rpcPort}" \
    --net-addr ":${toString netPort}" \
    --network "${network}" ${builtins.concatStringsSep " " options}
  '';
  common = import ./common.nix { inherit lib; inherit pkgs; };
  instanceOptions = types.submodule ( {...} : {
    options = common.sharedOptions // {
      enable = mkEnableOption "Tezos node service";

      package = mkOption {
        default = tezos-node-pkg;
        type = types.package;
      };

      rpcPort = mkOption {
        type = types.int;
        default = 8732;
        example = 8732;
        description = ''
          Tezos node RPC port.
        '';
      };

      netPort = mkOption {
        type = types.int;
        default = 9732;
        example = 9732;
        description = ''
          Tezos node net port.
        '';
      };

      network = mkOption {
        type = types.str;
        default = "ithacanet";
        description = ''
          Network which node will be running on.
          Can be either a predefined network name or a URL to the network config.
        '';
      };

      historyMode = mkOption {
        type = types.enum [ "full" "experimental-rolling" "archive" ];
        default = "full";
        description = ''
          Node history mode. Possible values are:
          full, experimental-rolling or archive.
        '';
      };

      additionalOptions = mkOption {
        type = types.listOf types.str;
        default = [];
        description = ''
          Additional 'tezos-node' options that affect configuration file.
        '';
      };

      nodeConfig = mkOption {
        default = null;
        type = types.nullOr (import sources.serokell-nix).lib.types.jsonConfig;
        description = ''
          Custom node config.
          This option overrides the all other options that affect
          tezos-node config.
        '';
      };
    };
  });
in {

  options.services.tezos-node = {
    instances = mkOption {
      type = types.attrsOf instanceOptions;
      description = "Configuration options";
      default = {};
    };
  };
  config = mkIf (cfg.instances != {}) {
    users = mkMerge (flip mapAttrsToList cfg.instances (node-name: node-cfg: common.genUsers node-name ));
    systemd = mkMerge (flip mapAttrsToList cfg.instances (node-name: node-cfg: {
      services."tezos-${node-name}-tezos-node" = common.genSystemdService node-name node-cfg "node" // {
        after = [ "network.target" ];
        preStart =
          ''
            node_data_dir="$STATE_DIRECTORY/node/data"
            mkdir -p "$node_data_dir"
          '' + (
            if node-cfg.nodeConfig == null
            then
              ''
                # Generate or update node config file
                if [[ ! -f "$node_data_dir/config.json" ]]; then
                  ${node-cfg.package}/bin/tezos-node config init \
                  ${genConfigCommand node-cfg.historyMode node-cfg.rpcPort node-cfg.netPort node-cfg.network node-cfg.additionalOptions}
                else
                  ${node-cfg.package}/bin/tezos-node config update \
                  ${genConfigCommand node-cfg.historyMode node-cfg.rpcPort node-cfg.netPort node-cfg.network node-cfg.additionalOptions}
                fi
              ''
            else
              ''
                cp ${node-cfg.nodeConfig} "$node_data_dir/config.json"
              ''
          );
        script = ''
          ${node-cfg.package}/bin/tezos-node run --data-dir "$STATE_DIRECTORY/node/data"
        '';
      };
    }));
  };
}
