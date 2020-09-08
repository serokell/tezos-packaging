# SPDX-FileCopyrightText: 2019 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: MPL-2.0

{ docker-binaries ? null, docker-arm-binaries ? null }:
let
  pkgs = import ./nix/build/pkgs.nix { };
  source = pkgs.ocamlPackages.tezos-client.src;

  meta = builtins.fromJSON (builtins.readFile ./meta.json);
  commonMeta = {
    version = pkgs.ocamlPackages.tezos-client.version;
    license = "MPL-2.0";
    dependencies = "";
    branchName = "v${pkgs.ocamlPackages.tezos-client.version}";
    licenseFile = "${source}/LICENSE";
  } // meta;
  release = pkgs.callPackage ./release.nix
    { binaries = docker-binaries; arm-binaries = docker-arm-binaries; inherit commonMeta; };

in { inherit release commonMeta pkgs; }
