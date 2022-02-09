# SPDX-FileCopyrightText: 2021 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ
pkgs:
{ self, nixpkgs, ... }:
import "${nixpkgs}/nixos/tests/make-test-python.nix" ({ ... }: {
  system = pkgs.system;
  inherit pkgs;

  machine = { ... }: {
    virtualisation.memorySize = 1024;
    virtualisation.diskSize = 1024;

    nixpkgs.pkgs = pkgs;
    imports = with self.nixosModules; [
      tezos-node
      tezos-signer
      tezos-accuser
      tezos-baker
    ];

    services.tezos-node.instances.ithacanet.enable = true;

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
}) {
  inherit pkgs;
  system = pkgs.system;
}
