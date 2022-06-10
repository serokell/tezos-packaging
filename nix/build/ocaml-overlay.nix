# SPDX-FileCopyrightText: 2021-2022 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

{ sources, protocols, pkgs, opam-nix, ... }:

self: super:
with opam-nix.lib.${pkgs.system}; let
  zcash-overlay = import ./zcash-overlay.nix;
  hacks = import ./hacks.nix;
  tezosSourcesResolved =
    pkgs.runCommand "resolve-tezos-sources" {} "cp --no-preserve=all -Lr ${sources.tezos} $out";
  tezosScope = buildOpamProject' {
    inherit pkgs;
    repos = [sources.opam-repository];
    recursive = true;
    resolveArgs = { };
  } tezosSourcesResolved { };
in {
  tezosPackages = (tezosScope.overrideScope' (pkgs.lib.composeManyExtensions [
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
    ]));
}
