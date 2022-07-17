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

  outputs = inputs@{ self, nixpkgs, nixpkgs-unstable, serokell-nix, nix, ... }:
  let
    system = "x86_64-linux";

    ocaml-overlay = callPackage ./nix/build/ocaml-overlay.nix {};

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

    pkgs-darwin = nixpkgs-unstable.legacyPackages."aarch64-darwin";

    callPackage = pkg: input:
      import pkg (inputs // { inherit sources protocols meta pkgs; } // input);

    protocols = pkgs.lib.importJSON ./protocols.json;

    meta = pkgs.lib.importJSON ./meta.json;

    sources = { inherit (inputs) tezos opam-repository; };

    binaries = callPackage ./nix {};

    tezos-release = callPackage ./release.nix {};

  in
  {
    nixosModules = {
      tezos-node = import ./nix/modules/tezos-node.nix;
      tezos-accuser = import ./nix/modules/tezos-accuser.nix;
      tezos-baker = import ./nix/modules/tezos-baker.nix;
      tezos-signer = import ./nix/modules/tezos-signer.nix;
    };

    legacyPackages.${system} = unstable;

    release = tezos-release;

    packages.${system} = binaries // { default = self.packages.${system}.binaries; };

    devShells.${system} = {
      buildkite = callPackage ./.buildkite/shell.nix {};
      autorelease = callPackage ./scripts/shell.nix {};
      autorelease-macos = callPackage ./scripts/macos-shell.nix { pkgs = pkgs-darwin; };
      dev = callPackage ./shell.nix { pkgs = unstable; };
    };

    checks.${system} = {
      tezos-nix-binaries = callPackage ./tests/tezos-nix-binaries.nix {};
      tezos-modules = callPackage ./tests/tezos-modules.nix {};
    };

    binaries-test = callPackage ./tests/tezos-binaries.nix {};
  };
}
