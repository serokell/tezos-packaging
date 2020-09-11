# SPDX-FileCopyrightText: 2019 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: MPL-2.0

{ sources ? import ./nix/sources.nix, tezos-source ? null
, protocols ? builtins.fromJSON (builtins.readFile ../../protocols.json)
, hacks ? import ./hacks.nix, pkgs ? import sources.nixpkgs { }
, opam-nix ? import sources.opam-nix pkgs }:
self: super:
let
  tezos-source-patched = self.stdenv.mkDerivation {
    name = "tezos-source-patched";
    src = tezos-source;
    phases = [ "unpackPhase" "patchPhase" "installPhase" ];
    patches = [ ./stdlib-unix.patch ];
    installPhase = "cp -r . $out";
  };

  tezos-source-eval = builtins.readFile "${tezos-source-patched}/LICENSE";
in
{
  ocamlPackages = self.ocaml-ng.ocamlPackages_4_09.overrideScope'
    (builtins.foldl' self.lib.composeExtensions (_: _: { }) [
      (opam-nix.traverseOPAMRepo' sources.opam-repository)
      (oself: osuper:
        if !isNull tezos-source then
          self.lib.filterAttrs (name: _: self.lib.hasPrefix "tezos-" name)
          (opam-nix.callOPAMPackage (builtins.deepSeq tezos-source-eval tezos-source-patched) oself osuper)
        else
          { })
      (oself: osuper: {
        inherit tezos-source;
      })
      (oself: osuper: {
        inherit ((opam-nix.callOPAMPackage
          (if isNull tezos-source then osuper.tezos-node.src else tezos-source))
          oself osuper)
          irmin irmin-pack;
      })
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
