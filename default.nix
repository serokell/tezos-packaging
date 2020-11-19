# SPDX-FileCopyrightText: 2019 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ

{ docker-binaries ? null, docker-arm-binaries ? null }:
let
  pkgs = import ./nix/build/pkgs.nix { };
  source = (import ./nix/nix/sources.nix).tezos;
  meta = builtins.fromJSON (builtins.readFile ./meta.json);
  commonMeta = {
    version = builtins.replaceStrings [ "refs/tags/v" ] [ "" ] source.ref;
    license = "MIT";
    dependencies = "";
    branchName = source.ref;
    licenseFile = "${source}/LICENSE";
  } // meta;
  release = pkgs.callPackage ./release.nix
    { binaries = docker-binaries; arm-binaries = docker-arm-binaries; inherit commonMeta; inherit (pkgs.lib) replaceStrings; };

in { inherit release commonMeta pkgs; }
