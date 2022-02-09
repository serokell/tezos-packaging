{
  inputs = {
    opam-nix.url = "github:tweag/opam-nix";
    tezos.url = "gitlab:tezos/tezos";
    tezos.flake = false;
    flake-utils.url = "github:numtide/flake-utils";
    nixpkgs.follows = "opam-nix/nixpkgs";
  };
  outputs = { self, flake-utils, opam-nix, tezos, nixpkgs }@inputs:
    let protocols = nixpkgs.lib.importJSON ../protocols.json;
    in rec {
      overlays = {
        hacks = import ./build/hacks.nix;
        nullify-protocols = import ./build/nullify-protocols.nix protocols;
      };
      overlay =
        nixpkgs.lib.composeManyExtensions (builtins.attrValues overlays);
      nixosModules = {
        tezos-accuser = import ./modules/tezos-accuser.nix;
        tezos-baker = import ./modules/tezos-baker.nix;
        tezos-endorser = import ./modules/tezos-endorser.nix;
        tezos-node = import ./modules/tezos-node.nix;
        tezos-signer = import ./modules/tezos-signer.nix;
      };
    } // flake-utils.lib.eachDefaultSystem (system:
      with opam-nix.lib.${system};
      let
        pkgs = nixpkgs.legacyPackages.${system};
        src = pkgs.runCommand "tezos-resolved" { }
          "cp --no-preserve=all -Lr ${tezos} $out";
        scope = buildOpamProject' {
          recursive = true;
          resolveArgs.dev = false;
        } src { ocaml-base-compiler = null; };

        release-binaries = builtins.filter (elem: elem.name != "tezos-sandbox")
          (import ./build/release-binaries.nix protocols);

        packages = builtins.listToAttrs (map (meta: {
          inherit (meta) name;
          value = ocamlPackages.${meta.name} // { inherit meta; };
        }) release-binaries);

        ocamlPackages = scope.overrideScope' self.overlay;
      in { inherit ocamlPackages packages; });
}
