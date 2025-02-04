# SPDX-FileCopyrightText: 2021 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ

{inputs}:
{config, lib, pkgs, ...}:

with lib;

let
  octez-signer-launch = "${pkgs.octezPackages.octez-signer}/bin/octez-signer launch";
  common = import ./common.nix { inherit lib pkgs inputs; };
  cfg = config.services.octez-signer;
  instanceOptions = types.submodule ( {...} : {
    options = common.sharedOptions // {

      enable = mkEnableOption "Octez signer service";

      networkProtocol = mkOption {
        type = types.enum [ "http" "https" "tcp" "unix" ];
        description = ''
          Network protocol version. Supports http, https, tcp and unix.
        '';
        example = "http";
      };

      netAddress = mkOption {
        type = types.str;
        default = "127.0.0.1";
        example = "127.0.0.1";
        description = ''
          Octez signer net address.
        '';
      };

      netPort = mkOption {
        type = types.int;
        default = 8080;
        example = 8080;
        description = ''
          Octez signer net port.
        '';
      };

      certPath = mkOption {
        type = types.str;
        default = null;
        description = ''
          Path of the SSL certificate to use for https Octez signer.
        '';
      };

      keyPath = mkOption {
        type = types.str;
        default = null;
        description = ''
          Key path to use for https Octez signer.
        '';
      };

      unixSocket = mkOption {
        type = types.str;
        default = null;
        description = ''
          Socket to use for Octez signer running over UNIX socket.
        '';
      };

      timeout = mkOption {
        type = types.int;
        default = 1;
        example = 1;
        description = ''
          Timeout for Octez signer.
        '';
      };

    };
  });
in {
  options.services.octez-signer = {
    instances = mkOption {
      type = types.attrsOf instanceOptions;
      description = "Configuration options";
      default = {};
    };
  };
  config = mkIf (cfg.instances != {}) {
    users = mkMerge (flip mapAttrsToList cfg.instances (node-name: node-cfg: common.genUsers node-name ));
    systemd = mkMerge (flip mapAttrsToList cfg.instances (node-name: node-cfg:
      let octez-signers = {
        "http" =
          "${octez-signer-launch} http signer --address ${node-cfg.netAddress} --port ${toString node-cfg.netPort}";
        "https" =
          "${octez-signer-launch} https signer ${node-cfg.certPath} ${node-cfg.keyPath} --address ${node-cfg.netAddress} --port ${toString node-cfg.netPort}";
        "tcp" =
          "${octez-signer-launch} socket signer --address ${node-cfg.netAddress} --port ${toString node-cfg.netPort} --timeout ${toString node-cfg.timeout}";
        "unix" =
          "${octez-signer-launch} local signer --socket ${node-cfg.unixSocket}";
      };
      in {
      services."tezos-${node-name}-octez-signer" = common.genSystemdService node-name node-cfg "signer" {} // {
        after = [ "network.target" ];
        script = ''
          ${octez-signers.${node-cfg.networkProtocol}}
        '';
      };
    }));
  };
}
