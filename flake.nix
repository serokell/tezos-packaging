# SPDX-FileCopyrightText: 2022 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

{
  description = "The tezos-packaging flake";

  nixConfig.flake-registry = "https://github.com/serokell/flake-registry/raw/master/flake-registry.json";

  inputs = {

    nixpkgs-unstable.url = "github:nixos/nixpkgs/nixos-unstable";

    nix.url = "github:nixos/nix";

    opam-nix.url = "github:tweag/opam-nix";

    flake-compat.flake = false;

    opam-repository.url = "gitlab:tezos/opam-repository";
    opam-repository.flake = false;

    tezos.url = "gitlab:tezos/tezos";
    tezos.flake = false;
  };

  outputs = inputs@{ self, nixpkgs, flake-utils, serokell-nix, nix, ... }: {

      nixosModules = {
        tezos-node = import ./nix/modules/tezos-node.nix;
        tezos-accuser = import ./nix/modules/tezos-accuser.nix;
        tezos-baker = import ./nix/modules/tezos-baker.nix;
        tezos-signer = import ./nix/modules/tezos-signer.nix;
      };

    } // flake-utils.lib.eachSystem [
      "x86_64-linux"
    ] (system:
    let

      ocaml-overlay = callPackage ./nix/build/ocaml-overlay.nix {};

      pkgs = import nixpkgs {
        inherit system;
        overlays = [
          serokell-nix.overlay
          ocaml-overlay
          (_: _: { inherit serokell-nix;
                   nix = nix.packages.${system}.default;
                 })
        ];
      };

      unstable = import inputs.nixpkgs-unstable {
        inherit system;
        overlays = [(_: _: { nix = nix.packages.${system}.default; })];
      };

      callPackage = pkg: input:
        import pkg (inputs // { inherit sources protocols meta pkgs; } // input);

      protocols = pkgs.lib.importJSON ./protocols.json;

      meta = pkgs.lib.importJSON ./meta.json;

      sources = { inherit (inputs) tezos opam-repository; };

      binaries = callPackage ./nix {};

      tezos-release = callPackage ./release.nix {};

    in rec {

      legacyPackages = pkgs;

      inherit tezos-release;

      apps.tezos-client = {
        type = "app";
        program = "${packages.tezos-client}/bin/tezos-client";
      };

      packages = binaries // { default = packages.binaries; };

      devShells = {
        buildkite = callPackage ./.buildkite/shell.nix {};
        autorelease = callPackage ./scripts/shell.nix {};
        autorelease-macos = callPackage ./scripts/macos-shell.nix {};
        dev = callPackage ./shell.nix { pkgs = unstable; };
      };

      checks = {
        tezos-nix-binaries = callPackage ./tests/tezos-nix-binaries.nix {};
        tezos-modules = callPackage ./tests/tezos-modules.nix {};
      };

      binaries-test = callPackage ./tests/tezos-binaries.nix {};
    });
}
