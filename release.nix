# SPDX-FileCopyrightText: 2019 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ

{ pkgs, sources, meta, protocols, ... }:
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
    binaries = ./binaries/docker;
    arm-binaries = ./arm-binaries/docker;
    inherit commonMeta protocols; inherit (pkgs.lib) replaceStrings;
  };

in { tezos-release = release; }
