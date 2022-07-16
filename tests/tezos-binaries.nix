# SPDX-FileCopyrightText: 2021 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

{ nixpkgs, pkgs, ... }: { path-to-binaries } @ args:
let
in import "${nixpkgs}/nixos/tests/make-test-python.nix" ({ ... }:
{
  nodes.machine = { ... }: {
    virtualisation.memorySize = 1024;
    virtualisation.diskSize = 1024;
    environment.sessionVariables.XDG_DATA_DIRS =
      [ "${pkgs.zcash}" ];
    security.pki.certificateFiles = [ ./ca.cert ];
  };

  testScript = ''
    path_to_binaries = "${path-to-binaries}"
    tezos_accuser = f"{path_to_binaries}/tezos-accuser-013-PtJakart"
    tezos_admin_client = f"{path_to_binaries}/tezos-admin-client"
    tezos_baker = f"{path_to_binaries}/tezos-baker-013-PtJakart"
    tezos_client = f"{path_to_binaries}/tezos-client"
    tezos_node = f"{path_to_binaries}/tezos-node"
    tezos_signer = f"{path_to_binaries}/tezos-signer"
    tezos_codec = f"{path_to_binaries}/tezos-codec"
    openssl = "${pkgs.openssl.bin}/bin/openssl"

    host_key = "${./host.key}"
    host_cert = "${./host.cert}"

    binaries = [
        tezos_accuser,
        tezos_admin_client,
        tezos_baker,
        tezos_client,
        tezos_node,
        tezos_signer,
        tezos_codec,
    ]
    ${builtins.readFile ./test_script.py}'';
}) args
