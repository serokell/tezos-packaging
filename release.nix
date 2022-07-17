# SPDX-FileCopyrightText: 2019 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ

{ pkgs, sources, meta, protocols, ... }: { docker-binaries, docker-arm-binaries }:
let
  source = sources.tezos;
  commonMeta = {
    version = builtins.replaceStrings [ "refs/tags/v" ] [ "" ] meta.tezos_ref;
    license = "MIT";
    dependencies = "";
    branchName = meta.tezos_ref;
    licenseFile = "${source}/LICENSE";
  } // meta;
  release = pkgs.callPackage ./tezos-release.nix {
    binaries = docker-binaries;
    arm-binaries = docker-arm-binaries;
    inherit commonMeta protocols; inherit (pkgs.lib) replaceStrings;
  };

in release
