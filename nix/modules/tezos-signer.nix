# SPDX-FileCopyrightText: 2021 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ

{config, lib, pkgs, ...}:

with lib;

let
  tezos-signer-launch = "${pkgs.ocamlPackages.tezos-signer}/bin/tezos-signer launch";
  common = import ./common.nix { inherit lib; inherit pkgs; };
  cfg = config.services.tezos-signer;
  instanceOptions = types.submodule ( {...} : {
    options = common.sharedOptions // {

      enable = mkEnableOption "Tezos signer service";

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
          Tezos signer net address.
        '';
      };

      netPort = mkOption {
        type = types.int;
        default = 8080;
        example = 8080;
        description = ''
          Tezos signer net port.
        '';
      };

      certPath = mkOption {
        type = types.str;
        default = null;
        description = ''
          Path of the SSL certificate to use for https Tezos signer.
        '';
      };

      keyPath = mkOption {
        type = types.str;
        default = null;
        description = ''
          Key path to use for https Tezos signer.
        '';
      };

      unixSocket = mkOption {
        type = types.str;
        default = null;
        description = ''
          Socket to use for Tezos signer running over UNIX socket.
        '';
      };

      timeout = mkOption {
        type = types.int;
        default = 1;
        example = 1;
        description = ''
          Timeout for Tezos signer.
        '';
      };

    };
  });
in {
  options.services.tezos-signer = {
    instances = mkOption {
      type = types.attrsOf instanceOptions;
      description = "Configuration options";
      default = {};
    };
  };
  config = mkIf (cfg.instances != {}) {
    users = mkMerge (flip mapAttrsToList cfg.instances (node-name: node-cfg: common.genUsers node-name ));
    systemd = mkMerge (flip mapAttrsToList cfg.instances (node-name: node-cfg:
      let tezos-signers = {
        "http" =
          "${tezos-signer-launch} http signer --address ${node-cfg.netAddress} --port ${toString node-cfg.netPort}";
        "https" =
          "${tezos-signer-launch} https signer ${node-cfg.certPath} ${node-cfg.keyPath} --address ${node-cfg.netAddress} --port ${toString node-cfg.netPort}";
        "tcp" =
          "${tezos-signer-launch} socket signer --address ${node-cfg.netAddress} --port ${toString node-cfg.netPort} --timeout ${toString node-cfg.timeout}";
        "unix" =
          "${tezos-signer-launch} local signer --socket ${node-cfg.unixSocket}";
      };
      in {
      services."tezos-${node-name}-tezos-signer" = common.genSystemdService node-name node-cfg "signer" // {
        after = [ "network.target" ];
        script = ''
          ${tezos-signers.${node-cfg.networkProtocol}}
        '';
      };
    }));
  };
}
