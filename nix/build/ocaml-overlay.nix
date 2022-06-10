# SPDX-FileCopyrightText: 2021-2022 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

{ sources ? import ../nix/sources.nix
, protocols ? builtins.fromJSON (builtins.readFile ../../protocols.json)
, hacks ? import ./hacks.nix, zcash-overlay ? import ./zcash-overlay.nix
, pkgs ? import sources.nixpkgs { }, opam-nix ? import sources.opam-nix }:

self: super:
with opam-nix.lib.${pkgs.system}; let
  tezosSourcesResolved =
    pkgs.runCommand "resolve-tezos-sources" {} "cp --no-preserve=all -Lr ${sources.tezos} $out";
  tezosScope = buildOpamProject' {
    inherit pkgs;
    repos = [sources.opam-repository];
    recursive = true;
    resolveArgs = { };
  } tezosSourcesResolved { };
in {
  ocamlPackages = (tezosScope.overrideScope' (pkgs.lib.composeManyExtensions [
      (_: # Nullify all the ignored protocols so that we don't build them
        builtins.mapAttrs (name: pkg:
          if builtins.any
          (proto: !isNull (builtins.match "tezos.*${proto}.*" name))
          protocols.ignored then
            null
          else
            pkg))
      hacks
      zcash-overlay
    ])) // pkgs.ocamlPackages;
}
