# SPDX-FileCopyrightText: 2019 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: MPL-2.0

{ patches ? [ ], date ? "Thu, 1 Jan 1970 10:00:00 +0300"
, builderInfo ? "", ubuntuVersion ? "bionic" }:
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

  inherit (import ../. {}) commonMeta;
  rpmMeta = { arch = "x86_64"; };
  debMeta = {
    arch = "amd64";
    inherit builderInfo ubuntuVersion date;
  };
  deb = builtins.mapAttrs
    (_: pkgs.callPackage ./package/deb.nix { meta = commonMeta // debMeta; }) binaries;
  rpm = builtins.mapAttrs
    (_: pkgs.callPackage ./package/rpm.nix { meta = commonMeta // rpmMeta; }) binaries;
  debSource = builtins.mapAttrs
    (_: pkgs.callPackage ./package/debSource.nix { meta = commonMeta // debMeta; })
    binaries;
  rpmSource = builtins.mapAttrs (_:
    pkgs.callPackage ./package/rpm.nix {
      meta = commonMeta // rpmMeta;
      buildSourcePackage = true;
    }) binaries;

  # Bundle the contents of a package set together, leaving the original attrs intact
  bundle = name: pkgSet:
    pkgSet // (pkgs.buildEnv {
      inherit name;
      paths = builtins.attrValues pkgSet;
    });

  artifacts = { inherit binaries deb rpm debSource rpmSource; };
  bundled = builtins.mapAttrs bundle artifacts;

in bundled
