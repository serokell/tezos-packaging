# SPDX-FileCopyrightText: 2021 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA
let
  nixpkgs = (import ../nix/nix/sources.nix).nixpkgs;
  pkgs = import ../nix/build/pkgs.nix {};
in import "${nixpkgs}/nixos/tests/make-test-python.nix" ({ ... }:
{
  machine = { ... }: {
    virtualisation.memorySize = 1024;
    virtualisation.diskSize = 1024;

    nixpkgs.pkgs = pkgs;
    imports = [ ../nix/modules/tezos-node.nix
                ../nix/modules/tezos-signer.nix
                ../nix/modules/tezos-accuser.nix
                ../nix/modules/tezos-baker.nix
              ];

    services.tezos-node.instances.ithacanet = {
      enable = true;
      additionalOptions = [
        "--bootstrap-threshold=1"
        "--connections" "50"
      ];
    };

    services.tezos-signer.instances.ithacanet = {
      enable = true;
      networkProtocol = "http";
    };

    services.tezos-accuser.instances.ithacanet = {
      enable = true;
      baseProtocol = "012-Psithaca";
    };

    services.tezos-baker.instances.ithacanet = {
      enable = true;
      baseProtocol = "012-Psithaca";
    };

  };

  testScript = ''
    start_all()

    services = [
        "tezos-node",
        "tezos-signer",
        "tezos-baker",
        "tezos-accuser",
    ]

    for s in services:
        machine.wait_for_unit(f"tezos-ithacanet-{s}.service")

    with subtest("check tezos-node rpc response"):
        machine.wait_for_open_port(8732)
        machine.wait_until_succeeds(
            "curl --silent http://localhost:8732/chains/main/blocks/head/header | grep level"
        )

    with subtest("service status sanity check"):
        for s in services:
            machine.succeed(f"systemctl status tezos-ithacanet-{s}.service")
  '';
})
