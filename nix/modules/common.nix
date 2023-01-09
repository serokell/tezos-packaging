# SPDX-FileCopyrightText: 2021 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

{ lib, pkgs, ... }:

with lib;
rec {
  sharedOptions = {

    logVerbosity = mkOption {
      type = types.enum [ "fatal" "error" "warning" "notice" "info" "debug" ];
      default = "warning";
      description = ''
        Level of logs verbosity. Possible values are:
        fatal, error, warn, notice, info or debug.
      '';
    };

  };

  daemonOptions = sharedOptions // {

    baseProtocols = mkOption {
      type = types.listOf (types.enum [ "PtLimaPt" ]);
      description = ''
        List of protocols for which daemons will be run.
      '';
      example = ["PtLimaPt"];
    };

    rpcPort = mkOption {
      type = types.int;
      default = 8732;
      example = 8732;
      description = ''
        Octez node RPC port.
      '';
    };

    passwordFilename = mkOption {
      type = types.nullOr types.path;
      default = null;
      description = ''
        Path to the file with passwords that can be used to decrypt encrypted keys.
      '';
    };
  };

  genDaemonConfig = { instancesCfg, service-name, service-pkgs, service-start-script, service-prestart-script ? (_: "")}:
    mkIf (instancesCfg != {}) {
      users = mkMerge (flip mapAttrsToList instancesCfg (node-name: node-cfg: genUsers node-name ));
      systemd = mkMerge (flip mapAttrsToList instancesCfg (node-name: node-cfg:
        let octez-client = "${pkgs.octezPackages.octez-client}/bin/octez-client";
            passwordFilenameArg = if node-cfg.passwordFilename != null then "-f ${node-cfg.passwordFilename}" else "";
        in {
          services."tezos-${node-name}-octez-${service-name}" = lib.recursiveUpdate (genSystemdService node-name node-cfg service-name) rec {
            bindsTo = [ "network.target" "tezos-${node-name}-octez-node.service" ];
            after = bindsTo;
            path = with pkgs; [ curl ];
            preStart =
              ''
                while ! _="$(curl --silent http://localhost:${toString node-cfg.rpcPort}/chains/main/blocks/head/)"; do
                  echo "Trying to connect to octez-node"
                  sleep 1s
                done

                service_data_dir="$STATE_DIRECTORY/client/data"
                mkdir -p "$service_data_dir"

                # Generate or update service config file
                if [[ ! -f "$service_data_dir/config" ]]; then
                  ${octez-client} -d "$service_data_dir" -E "http://localhost:${toString node-cfg.rpcPort}" ${passwordFilenameArg} \
                  config init --output "$service_data_dir/config" >/dev/null 2>&1
                else
                  ${octez-client} -d "$service_data_dir" -E "http://localhost:${toString node-cfg.rpcPort}" ${passwordFilenameArg} \
                  config update >/dev/null 2>&1
                fi
              '' + service-prestart-script node-cfg;
            script = service-start-script node-cfg;
            serviceConfig = {
              Type = "forking";
            };
          };
      }));
    };

  genUsers = node-name: {
    groups."tezos-${node-name}" = { };
    users."tezos-${node-name}" = { group = "tezos-${node-name}"; isNormalUser = true; };
  };

  genSystemdService = node-name: node-cfg: service-name: {
    wantedBy = [ "multi-user.target" ];
    description = "Octez ${service-name}";
    environment = {
      OCTEZ_LOG = "* -> ${node-cfg.logVerbosity}";
    };
    serviceConfig = {
      User = "tezos-${node-name}";
      Group = "tezos-${node-name}";
      StateDirectory = "tezos-${node-name}";
      Restart = "always";
      RestartSec = "10";
    };
  };

}
