{
  inputs = {
    opam-nix.url = "github:tweag/opam-nix";
    tezos.url = "gitlab:tezos/tezos";
    tezos.flake = false;
    flake-utils.url = "github:numtide/flake-utils";
    nixpkgs.follows = "opam-nix/nixpkgs";
    serokell-nix.url = "github:serokell/serokell.nix";
  };
  outputs =
    { self, flake-utils, opam-nix, tezos, nixpkgs, serokell-nix }@inputs:
    let protocols = nixpkgs.lib.importJSON ./protocols.json;
    in rec {
      ocaml-overlays = {
        hacks = import ./nix/build/hacks.nix;
        nullify-protocols = import ./nix/build/nullify-protocols.nix protocols;
        zcash = import ./nix/build/zcash-overlay.nix;
      };
      ocaml-overlay =
        nixpkgs.lib.composeManyExtensions (builtins.attrValues ocaml-overlays);
      overlay = final: prev:
        with opam-nix.lib.${final.system};
        let
          pkgs = final;
          src = pkgs.runCommand "tezos-resolved" { }
            "cp --no-preserve=all -Lr ${tezos} $out";
          scope = buildOpamProject' {
            recursive = true;
            resolveArgs.dev = false;
          } src { ocaml-base-compiler = null; };

          release-binaries =
            builtins.filter (elem: elem.name != "tezos-sandbox")
            (import ./nix/build/release-binaries.nix protocols);

          packages = builtins.listToAttrs (map (meta: {
            inherit (meta) name;
            value = ocamlPackages.${meta.name} // { inherit meta; };
          }) release-binaries);
          ocamlPackages = scope.overrideScope' self.ocaml-overlay;

        in {
          tezosPackages = packages;
          tezosScope = ocamlPackages;
        };
      nixosModules = {
        tezos-accuser = import ./nix/modules/tezos-accuser.nix;
        tezos-baker = import ./nix/modules/tezos-baker.nix;
        tezos-endorser = import ./nix/modules/tezos-endorser.nix;
        tezos-node = import ./nix/modules/tezos-node.nix inputs;
        tezos-signer = import ./nix/modules/tezos-signer.nix;
      };
    } // flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        checks = {
          binaries = import ./tests/tezos-nix-binaries.nix applied inputs;
          modules = import ./tests/tezos-modules.nix applied inputs;
        };

        applied = pkgs.extend (pkgs.lib.composeManyExtensions [
          self.overlay
          serokell-nix.overlay
        ]);
      in {
        inherit checks;
        packages = applied.tezosPackages;
        ocamlPackages = applied.tezosScope;

        # Use with
        # nix eval .#binaries-test.x86_64-linux --apply "(m: m ./path/to/binaries)"
        binaries-test = import ./tests/tezos-binaries.nix applied inputs;
      });
}
