# SPDX-FileCopyrightText: 2019 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: MPL-2.0

{ sources ? import ./nix/sources.nix
, protocols ? builtins.fromJSON (builtins.readFile ../../protocols.json)
, hacks ? import ./hacks.nix, pkgs ? import sources.nixpkgs { }
, opam-nix ? import sources.opam-nix pkgs }:
self: super: {
  ocamlPackages = self.ocaml-ng.ocamlPackages_4_09.overrideScope'
    (builtins.foldl' self.lib.composeExtensions (_: _: { }) [
      (opam-nix.traverseOPAMRepo' sources.opam-repository)
      (oself: osuper: { inherit ((opam-nix.callOPAMPackage osuper.tezos-node.src) oself osuper) irmin irmin-pack; })
      (_: # Nullify all the ignored protocols so that we don't build them
        builtins.mapAttrs (name: pkg:
          if builtins.any
          (proto: !isNull (builtins.match "tezos.*${proto}.*" name))
          protocols.ignored then
            null
          else
            pkg))
      (oself: osuper:
        builtins.mapAttrs (name: pkg:
          if self.lib.hasPrefix "tezos" name && pkg ? override then
            pkg.override { dune = oself.dune_2; }
          else
            pkg) osuper)
      (hacks self super)
      (opam-nix.cacheSources sources)
    ]);
}
