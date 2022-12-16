# SPDX-FileCopyrightText: 2021 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

{ nixpkgs, pkgs, ... }: { path-to-binaries } @ args:
let
in import "${nixpkgs}/nixos/tests/make-test-python.nix" ({ ... }:
{
  name = "tezos-binaries-test";
  nodes.machine = { ... }: {
    virtualisation.memorySize = 2048;
    virtualisation.diskSize = 1024;
    environment.sessionVariables.XDG_DATA_DIRS =
      [ "${pkgs.zcash-params}" ];
    security.pki.certificateFiles = [ ./ca.cert ];
  };

  testScript = ''
    path_to_binaries = "${path-to-binaries}"
    octez_accuser = f"{path_to_binaries}/octez-accuser-PtKathma"
    octez_admin_client = f"{path_to_binaries}/octez-admin-client"
    octez_baker = f"{path_to_binaries}/octez-baker-PtKathma"
    octez_client = f"{path_to_binaries}/octez-client"
    octez_node = f"{path_to_binaries}/octez-node"
    octez_signer = f"{path_to_binaries}/octez-signer"
    octez_codec = f"{path_to_binaries}/octez-codec"
    openssl = "${pkgs.openssl.bin}/bin/openssl"

    host_key = "${./host.key}"
    host_cert = "${./host.cert}"

    binaries = [
        octez_accuser,
        octez_admin_client,
        octez_baker,
        octez_client,
        octez_node,
        octez_signer,
        octez_codec,
    ]
    ${builtins.readFile ./test_script.py}'';
}) args
