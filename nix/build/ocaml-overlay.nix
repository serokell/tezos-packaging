# SPDX-FileCopyrightText: 2021-2022 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

{ sources, protocols, opam-nix, ... }:

self: super:
let
  pkgs = super;
in
with opam-nix.lib.${self.system}; let
  zcash-overlay = import ./zcash-overlay.nix;
  hacks = import ./hacks.nix;
  octezSourcesResolved =
    self.runCommand "resolve-octez-sources" {} "cp --no-preserve=all -Lr ${sources.tezos} $out";
  octezScope = buildOpamProject' {
    repos = [sources.opam-repository];
    recursive = true;
    resolveArgs = { };
  } octezSourcesResolved { };
in {
  octezPackages = (octezScope.overrideScope' (pkgs.lib.composeManyExtensions [
      (_: # Nullify all the ignored protocols so that we don't build them
        builtins.mapAttrs (name: pkg:
          if builtins.any
          (proto: !isNull (builtins.match ".*${proto}.*" name))
          protocols.ignored then
            null
          else
            pkg))
      hacks
      zcash-overlay
    ]));
}
