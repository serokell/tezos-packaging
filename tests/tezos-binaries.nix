# SPDX-FileCopyrightText: 2020 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ
{ path-to-binaries ? null } @ args:
let
  nixpkgs = (import ../nix/nix/sources.nix).nixpkgs;
in import "${nixpkgs}/nixos/tests/make-test-python.nix" ({ pkgs, ... }:
{
  nodes.machine = { ... }: { virtualisation.memorySize = 1024; };

  testScript = ''
    path_to_binaries = "${path-to-binaries}"
    tezos_accuser = f"{path_to_binaries}/tezos-accuser-007-PsDELPH1"
    tezos_admin_client = f"{path_to_binaries}/tezos-admin-client"
    tezos_baker = f"{path_to_binaries}/tezos-baker-007-PsDELPH1"
    tezos_client = f"{path_to_binaries}/tezos-client"
    tezos_endorser = f"{path_to_binaries}/tezos-endorser-007-PsDELPH1"
    tezos_node = f"{path_to_binaries}/tezos-node"
    tezos_signer = f"{path_to_binaries}/tezos-signer"
    tezos_codec = f"{path_to_binaries}/tezos-codec"
    openssl = "${pkgs.openssl.bin}/bin/openssl"
    binaries = [
        tezos_accuser,
        tezos_admin_client,
        tezos_baker,
        tezos_client,
        tezos_endorser,
        tezos_node,
        tezos_signer,
        tezos_codec,
    ]
    ${builtins.readFile ./test_script.py}'';
}) args
