# SPDX-FileCopyrightText: 2022 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

{
  description = "The tezos-packaging flake";

  nixConfig.flake-registry = "https://github.com/serokell/flake-registry/raw/master/flake-registry.json";

  inputs = {

    nixpkgs-unstable.url = "github:nixos/nixpkgs/nixos-unstable";

    nixpkgs.url = "github:serokell/nixpkgs";

    nix.url = "github:nixos/nix";

    opam-nix.url = "github:tweag/opam-nix";

    rust-overlay.url = "github:oxalica/rust-overlay";

    crane.url = "github:ipetkov/crane";

    flake-compat.flake = false;

    opam-repository.url = "github:ocaml/opam-repository";
    opam-repository.flake = false;

    tezos.url = "gitlab:tezos/tezos";
    tezos.flake = false;
  };

  outputs = inputs@{ self, nixpkgs, nixpkgs-unstable, flake-utils, serokell-nix, nix, rust-overlay, crane, ... }:
  let
    pkgs = import nixpkgs { system = "x86_64-linux"; };
    pkgs-unstable = import nixpkgs-unstable { system = "x86_64-linux"; overlays = [ rust-overlay.overlays.default ]; };
    pkgs-darwin = nixpkgs-unstable.legacyPackages."aarch64-darwin";
    protocols = nixpkgs.lib.importJSON ./protocols.json;
    meta = nixpkgs.lib.importJSON ./meta.json;

    tezos = builtins.path {
      path = inputs.tezos;
      name = "tezos";
      # we exclude optional development packages
      filter = path: _: !(builtins.elem (baseNameOf path) [ "lib_parameters" "octez-dev-deps.opam" "tezos-time-measurement.opam" ]);
    };

    toolchain-version = pkgs-unstable.lib.strings.trim (builtins.readFile "${tezos}/rust-toolchain");

    rust-toolchain = pkgs-unstable.rust-bin.stable.${toolchain-version}.default;

    craneLib = (crane.mkLib pkgs-unstable).overrideToolchain (p: p.rust-bin.stable.${toolchain-version}.default);

    opam-repository = pkgs.stdenv.mkDerivation {
      name = "opam-repository";
      src = inputs.opam-repository;
      phases = [ "unpackPhase" "patchPhase" "installPhase" ];
      patchPhase = ''
        mkdir -p packages/octez-deps/octez-deps.dev
        cp ${tezos}/opam/virtual/octez-deps.opam.locked packages/octez-deps/octez-deps.dev/opam
        mkdir -p packages/stdcompat/stdcompat.19
        cp ${tezos}/opam/virtual/stdcompat.opam.locked packages/stdcompat/stdcompat.19/opam

        # This package adds some constraints to the solution found by the opam solver.
        dummy_pkg=octez-dummy
        dummy_opam_dir="packages/$dummy_pkg/$dummy_pkg.dev"
        dummy_opam="$dummy_opam_dir/opam"
        mkdir -p "$dummy_opam_dir"
        echo 'opam-version: "2.0"' > "$dummy_opam"
        echo "depends: [ \"ocaml\" { = \"$ocaml_version\" } ]" >> "$dummy_opam"
        echo 'conflicts:[' >> "$dummy_opam"
        grep -r "^flags: *\[ *avoid-version *\]" -l packages |
          LC_COLLATE=C sort -u |
          while read -r f; do
            f=$(dirname "$f")
            f=$(basename "$f")
            p=$(echo "$f" | cut -d '.' -f '1')
            v=$(echo "$f" | cut -d '.' -f '2-')
            echo "\"$p\" {= \"$v\"}" >> $dummy_opam
          done
        # FIXME: https://gitlab.com/tezos/tezos/-/issues/5832
        # opam unintentionally picks up a windows dependency. We add a
        # conflict here to work around it.
        echo '"ocamlbuild" {= "0.14.2+win" }' >> $dummy_opam
        echo ']' >> "$dummy_opam"

        OPAMSOLVERTIMEOUT=600 ${pkgs.opam}/bin/opam admin filter --yes --resolve \
          "octez-deps,ocaml,ocaml-base-compiler,odoc,ledgerwallet-tezos,caqti-driver-postgresql,$dummy_pkg,ounit2,ctypes-foreign" \
          --environment "os=linux,arch=x86_64,os-family=debian"

        rm -rf packages/"$dummy_pkg" packages/octez-deps
      '';

      installPhase = ''
        mkdir -p $out
        cp -Lpr * $out
      '';
    };

    sources = { inherit tezos opam-repository; };

    ocaml-overlay = import ./nix/build/ocaml-overlay.nix (inputs // { inherit sources protocols meta craneLib rust-toolchain; });
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

      overlays.default = final: prev: nixpkgs.lib.composeManyExtensions [
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

      inherit (callPackage ./nix {}) octez-binaries tezos-binaries;

      release = callPackage ./release.nix {};

    in {

      legacyPackages = unstable;

      inherit release;

      packages = octez-binaries // tezos-binaries
        // { default = pkgs.linkFarmFromDrvs "binaries" (builtins.attrValues octez-binaries); };

      ocaml-packages = pkgs.octezPackages;

      devShells = {
        buildkite = callPackage ./.buildkite/shell.nix {};
        autorelease = callPackage ./scripts/shell.nix {};
        docker-tezos-packages = callPackage ./shell.nix {};
      };

      checks = {
        tezos-nix-binaries = callPackage ./tests/tezos-nix-binaries.nix {};
        tezos-modules = callPackage ./tests/tezos-modules.nix {};
      };

      binaries-test = callPackage ./tests/tezos-binaries.nix {};
    }));
}
