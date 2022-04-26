# SPDX-FileCopyrightText: 2021 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA
let
  nixpkgs = (import ../nix/nix/sources.nix).nixpkgs;
  pkgs = import ../nix/build/pkgs.nix {};
  inherit (pkgs.ocamlPackages) tezos-client tezos-admin-client tezos-node tezos-signer tezos-codec
    tezos-accuser-013-PtJakart tezos-baker-013-PtJakart;
in import "${nixpkgs}/nixos/tests/make-test-python.nix" ({ ... }:
{
  nodes.machine = { ... }: {
    virtualisation.memorySize = 1024;
    virtualisation.diskSize = 1024;
    environment.systemPackages = with pkgs; [
      libev
    ];
    security.pki.certificateFiles = [ ./ca.cert ];
    environment.sessionVariables.LD_LIBRARY_PATH =
      [ "${pkgs.ocamlPackages.hacl-star-raw}/lib/ocaml/4.12.0/site-lib/hacl-star-raw" ];
  };

  testScript = ''
    tezos_accuser = "${tezos-accuser-013-PtJakart}/bin/tezos-accuser-013-PtJakart"
    tezos_admin_client = "${tezos-admin-client}/bin/tezos-admin-client"
    tezos_baker = "${tezos-baker-013-PtJakart}/bin/tezos-baker-013-PtJakart"
    tezos_client = (
        "${tezos-client}/bin/tezos-client"
    )
    tezos_node = "${tezos-node}/bin/tezos-node"
    tezos_signer = (
        "${tezos-signer}/bin/tezos-signer"
    )
    tezos_codec = "${tezos-codec}/bin/tezos-codec"
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
})
