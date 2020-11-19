# SPDX-FileCopyrightText: 2019 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ

{ patches ? [ ] }:
let
  pkgs = import ./build/pkgs.nix { };
  source = (import ./nix/sources.nix).tezos;
  protocols = import ./protocols.nix;
  bin = pkgs.callPackage ./build/bin.nix { };
  release-binaries = import ./build/release-binaries.nix;
  binaries = builtins.listToAttrs (map (meta: {
    inherit (meta) name;
    value = bin pkgs.pkgsMusl.ocamlPackages.${meta.name} // { inherit meta; };
  }) release-binaries);

  # Bundle the contents of a package set together, leaving the original attrs intact
  bundle = name: pkgSet:
    pkgSet // (pkgs.buildEnv {
      inherit name;
      paths = builtins.attrValues pkgSet;
    });

  artifacts = { inherit binaries; };
  bundled = builtins.mapAttrs bundle artifacts;

in bundled
