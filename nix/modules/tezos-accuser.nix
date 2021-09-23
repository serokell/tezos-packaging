# SPDX-FileCopyrightText: 2021 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ

{config, lib, pkgs, ...}:

with lib;

let
  tezos-accuser-pkgs = {
    "010-PtGRANAD" =
      "${pkgs.ocamlPackages.tezos-accuser-010-PtGRANAD}/bin/tezos-accuser-010-PtGRANAD";
    "011-PtHangzH" =
      "${pkgs.ocamlPackages.tezos-accuser-011-PtHangzH}/bin/tezos-accuser-011-PtHangzH";
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
    let accuser-script = node-cfg: ''
        ${tezos-accuser-pkgs.${node-cfg.baseProtocol}} -d "$STATE_DIRECTORY/client/data" \
        -E "http://localhost:${toString node-cfg.rpcPort}" \
        run "$@"
      '';
    in common.genDaemonConfig cfg.instances "accuser" tezos-accuser-pkgs accuser-script;
}
