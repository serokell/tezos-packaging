# SPDX-FileCopyrightText: 2021 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA
{ nixpkgs, pkgs, ... }:
let
  inherit (pkgs) system;
  inherit (pkgs.octezPackages)
    octez-client octez-admin-client octez-node octez-signer octez-codec
    octez-accuser-PtNairob octez-baker-PtNairob;
in import "${nixpkgs}/nixos/tests/make-test-python.nix" ({ ... }: {
  name = "tezos-nix-binaries-test";
  nodes.machine = { ... }: {
    virtualisation.memorySize = 1024;
    virtualisation.diskSize = 1024;
    environment.systemPackages = with pkgs; [ libev ];
    security.pki.certificateFiles = [ ./ca.cert ];
    environment.sessionVariables.LD_LIBRARY_PATH = [
      "${pkgs.ocamlPackages.hacl-star-raw}/lib/ocaml/4.12.0/site-lib/hacl-star-raw"
    ];
  };

  testScript = ''
    octez_accuser = "${octez-accuser-PtNairob}/bin/octez-accuser-PtNairob"
    octez_admin_client = "${octez-admin-client}/bin/octez-admin-client"
    octez_baker = "${octez-baker-PtNairob}/bin/octez-baker-PtNairob"
    octez_client = (
        "${octez-client}/bin/octez-client"
    )
    octez_node = "${octez-node}/bin/octez-node"
    octez_signer = (
        "${octez-signer}/bin/octez-signer"
    )
    octez_codec = "${octez-codec}/bin/octez-codec"
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
}) { inherit pkgs system; }
