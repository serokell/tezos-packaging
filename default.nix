# SPDX-FileCopyrightText: 2019 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: MPL-2.0

{ docker-binaries ? null }:
let
  pkgs = import ./nix/build/pkgs.nix { };
  source = (import ./nix/nix/sources.nix).tezos;
  commonMeta = {
    # release should be updated in case we change something
    release = "2";
    # we switched from time-based versioning to proper tezos versioning
    epoch = "1";
    version = builtins.replaceStrings [ "v" ] [ "" ] source.ref;
    license = "MPL-2.0";
    dependencies = "";
    maintainer = "Serokell https://serokell.io <hi@serokell.io>";
    branchName = source.ref;
    licenseFile = "${source}/LICENSE";
  };
  release =
    pkgs.callPackage ./release.nix { binaries = docker-binaries; inherit commonMeta; };

in { inherit release commonMeta; }
