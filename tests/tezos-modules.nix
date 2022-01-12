# SPDX-FileCopyrightText: 2021 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ
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

    services.tezos-node.instances.hangzhounet.enable = true;

    services.tezos-signer.instances.hangzhounet = {
      enable = true;
      networkProtocol = "http";
    };

    services.tezos-accuser.instances.hangzhounet = {
      enable = true;
      baseProtocol = "011-PtHangz2";
    };

    services.tezos-baker.instances.hangzhounet = {
      enable = true;
      baseProtocol = "011-PtHangz2";
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
        machine.wait_for_unit(f"tezos-hangzhounet-{s}.service")

    with subtest("check tezos-node rpc response"):
        machine.wait_for_open_port(8732)
        machine.wait_until_succeeds(
            "curl --silent http://localhost:8732/chains/main/blocks/head/header | grep level"
        )

    with subtest("service status sanity check"):
        for s in services:
            machine.succeed(f"systemctl status tezos-hangzhounet-{s}.service")
  '';
})
