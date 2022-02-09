# SPDX-FileCopyrightText: 2020 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ
pkgs:
{ self, nixpkgs, ... }:
let
  system = pkgs.system;
  inherit (self.ocamlPackages.${system}) tezos-client tezos-admin-client tezos-node tezos-signer tezos-codec
    tezos-accuser-012-Psithaca tezos-baker-012-Psithaca;
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
    tezos_accuser = "${tezos-accuser-012-Psithaca}/bin/tezos-accuser-012-Psithaca"
    tezos_admin_client = "${tezos-admin-client}/bin/tezos-admin-client"
    tezos_baker = "${tezos-baker-012-Psithaca}/bin/tezos-baker-012-Psithaca"
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
}) { inherit pkgs system; }
