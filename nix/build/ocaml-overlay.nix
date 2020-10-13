# SPDX-FileCopyrightText: 2019 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: MPL-2.0

{ sources ? import ../nix/sources.nix
, protocols ? builtins.fromJSON (builtins.readFile ../../protocols.json)
, hacks ? import ./hacks.nix
, pkgs ? import sources.nixpkgs { }, opam-nix ? import sources.opam-nix pkgs }:
self: super: {
  ocamlPackages = self.ocaml-ng.ocamlPackages_4_09.overrideScope'
    (builtins.foldl' self.lib.composeExtensions (_: _: { }) [
      (opam-nix.traverseOPAMRepo' sources.opam-repository)
      (oself: osuper: { index-super = osuper.index.versions."1.2.0"; })
      (opam-nix.callOPAMPackage sources.tezos)
      (_: # Nullify all the ignored protocols so that we don't build them
        builtins.mapAttrs (name: pkg:
          if builtins.any
          (proto: !isNull (builtins.match "tezos.*${proto}.*" name))
          protocols.ignored then
            null
          else
            pkg))
      (hacks self super)
      (opam-nix.cacheSources sources)
    ]);
}
