# SPDX-FileCopyrightText: 2021 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA
{ nixpkgs, pkgs, ... }:
let
  inherit (pkgs) system;

  octez-node = {
    enable = true;
    additionalOptions = [
      "--bootstrap-threshold=1"
      "--connections" "50"
    ];
  };

  octez-signer = {
    enable = true;
    networkProtocol = "http";
  };

  octez-accuser = {
    enable = true;
    baseProtocols = ["PsParisC"];
  };

  octez-baker = {
    enable = true;
    baseProtocols = ["PsParisC"];
    bakerAccountAlias = "baker";
    bakerSecretKey = "unencrypted:edsk3KaTNj1d8Xd3kMBrZkJrfkqsz4XwwiBXatuuVgTdPye2KpE98o";
  };
in
import "${nixpkgs}/nixos/tests/make-test-python.nix" ({ ... }:
{
  name = "tezos-modules-test";
  machine = { ... }: {
    virtualisation.memorySize = 1024;
    virtualisation.diskSize = 1024;

    nixpkgs.pkgs = pkgs;
    imports = [ ../nix/modules/tezos-node.nix
                ../nix/modules/tezos-signer.nix
                ../nix/modules/tezos-accuser.nix
                ../nix/modules/tezos-baker.nix
              ];

    services = {
      octez-node.instances.ghostnet = octez-node;
      octez-signer.instances.ghostnet = octez-signer;
      octez-accuser.instances.ghostnet = octez-accuser;
      octez-baker.instances.ghostnet = octez-baker;
    };

  };

  testScript = ''
    from typing import List

    start_all()

    services: List[str] = [
        ${if octez-node.enable then ''"octez-node",'' else ""}
        ${if octez-signer.enable then ''"octez-signer",'' else ""}
        ${if octez-accuser.enable then ''"octez-accuser",'' else ""}
        ${if octez-baker.enable then ''"octez-baker",'' else ""}
    ]

    for s in services:
        machine.wait_for_unit(f"tezos-ghostnet-{s}.service")

    ${if octez-node.enable then ''
    with subtest("check octez-node rpc response"):
        machine.wait_for_open_port(8732)
        machine.wait_until_succeeds(
            "curl --silent http://localhost:8732/chains/main/blocks/head/header | grep level"
        )
    '' else ""}


    with subtest("service status sanity check"):
        for s in services:
            machine.succeed(f"systemctl status tezos-ghostnet-{s}.service")
  '';
}) { inherit pkgs system; }
