# SPDX-FileCopyrightText: 2022 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

{
  description = "The tezos-packaging flake";

  nixConfig.flake-registry = "https://github.com/serokell/flake-registry/raw/master/flake-registry.json";

  inputs = {

    nixpkgs-unstable.url = "github:nixos/nixpkgs/nixos-unstable";

    nix.url = "github:nixos/nix";

    opam-nix.url = "github:tweag/opam-nix";
    opam-nix.inputs.opam-repository.follows = "opam-repository";

    flake-compat.flake = false;

    opam-repository.url = "gitlab:tezos/opam-repository";
    opam-repository.flake = false;

    tezos.url = "gitlab:tezos/tezos";
    tezos.flake = false;
  };

  outputs = inputs@{ self, nixpkgs, nixpkgs-unstable, flake-utils, serokell-nix, nix, ... }:
  let
    pkgs-darwin = nixpkgs-unstable.legacyPackages."aarch64-darwin";

    protocols = nixpkgs.lib.importJSON ./protocols.json;
    meta = nixpkgs.lib.importJSON ./meta.json;
    sources = { inherit (inputs) tezos opam-repository; };

    ocaml-overlay = import ./nix/build/ocaml-overlay.nix (inputs // { inherit sources protocols meta; });
  in pkgs-darwin.lib.recursiveUpdate
  {
      nixosModules = {
        tezos-node = import ./nix/modules/tezos-node.nix;
        tezos-accuser = import ./nix/modules/tezos-accuser.nix;
        tezos-baker = import ./nix/modules/tezos-baker.nix;
        tezos-signer = import ./nix/modules/tezos-signer.nix;
      };

      devShells."aarch64-darwin".autorelease-macos =
        import ./scripts/macos-shell.nix { pkgs = pkgs-darwin; };

      overlay = final: prev: nixpkgs.lib.composeManyExtensions [
        ocaml-overlay
        (final: prev: { inherit (inputs) serokell-nix; })
      ] final prev;
  } (flake-utils.lib.eachSystem [
      "x86_64-linux"
    ] (system:
    let

      overlay = final: prev: {
        inherit (inputs) serokell-nix;
        nix = nix.packages.${system}.default;
        zcash-params = callPackage ./nix/build/zcash.nix {};
      };

      pkgs = import nixpkgs {
        inherit system;
        overlays = [
          overlay
          serokell-nix.overlay
          ocaml-overlay
        ];
      };

      unstable = import nixpkgs-unstable {
        inherit system;
        overlays = [(_: _: { nix = nix.packages.${system}.default; })];
      };

      callPackage = pkg: input:
        import pkg (inputs // { inherit sources protocols meta pkgs; } // input);

      binaries = callPackage ./nix {};

      release = callPackage ./release.nix {};

    in {

      legacyPackages = unstable;

      inherit release;

      packages = binaries // { default = self.packages.${system}.binaries; };

      devShells = {
        buildkite = callPackage ./.buildkite/shell.nix {};
        autorelease = callPackage ./scripts/shell.nix {};
        dev = callPackage ./shell.nix { pkgs = unstable; };
      };

      checks = {
        tezos-nix-binaries = callPackage ./tests/tezos-nix-binaries.nix {};
        tezos-modules = callPackage ./tests/tezos-modules.nix {};
      };

      binaries-test = callPackage ./tests/tezos-binaries.nix {};
    }));
}
