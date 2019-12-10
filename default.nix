# SPDX-FileCopyrightText: 2019 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: MPL-2.0
{ pkgs ? import <nixpkgs> { }, timestamp ? "19700101" }:
with pkgs;

let
  root = ./.;
  mainnet = {
    rev = "94f779a7";
    sha256 = "16lxilng5q8fr2ll6h4hf7wlvac6nmw4cx10cbgzj5ks090bl97r";
    patchFile = ./nix/fix-mainnet.patch;
    protoName = "proto_005_PsBabyM1";
  };
  babylonnet = {
    rev = "b8731913";
    sha256 = "1pakf1s6bg76fq42mb8fj1immz9g9wwimd522cpx8k28zf0hkl5i";
    patchFile = ./nix/fix-babylonnet.patch;
    protoName = "proto_005_PsBabyM1";
  };
  static-nix = import ./nix/static.nix;
  tezos-static-mainnet = static-nix mainnet;
  tezos-static-babylonnet = static-nix babylonnet;
  binary-mainnet = "${tezos-static-mainnet}/bin/tezos-client";
  binary-babylonnet = "${tezos-static-babylonnet}/bin/tezos-client";
  packageDesc-mainnet = {
    inherit licenseFile;
    project = "tezos-client-mainnet";
    version = toString timestamp;
    bin = binary-mainnet;
    arch = "amd64";
    license = "MIT";
    dependencies = "";
    maintainer = "Serokell https://serokell.io";
    description = "CLI client for interacting with tezos blockchain";
    gitRevision = mainnet.rev;
    branchName = "mainnet";
  };

  packageDesc-babylonnet = packageDesc-mainnet // {
    project = "tezos-client-babylonnet";
    bin = binary-babylonnet;
    gitRevision = babylonnet.rev;
    branchName = "babylonnet";
  };

  buildDeb = import ./packageDeb.nix { inherit stdenv writeTextFile dpkg; };
  buildRpm = packageDesc:
  import ./packageRpm.nix { inherit stdenv writeTextFile gnutar rpm buildFHSUserEnv; }
    (packageDesc // { arch = "x86_64"; });

  mainnet-rpm-package = buildRpm packageDesc-mainnet;

  mainnet-deb-package = buildDeb packageDesc-mainnet;

  babylonnet-rpm-package = buildRpm packageDesc-babylonnet;

  babylonnet-deb-package = buildDeb packageDesc-babylonnet;

  tezos-client-mainnet = stdenv.mkDerivation rec {
    name = "tezos-client-mainnet-${mainnet.rev}";
    phases = "copyPhase";
    copyPhase = ''
      mkdir -p $out
      cp ${binary-mainnet} $out/${name}
    '';
  };
  tezos-client-babylonnet = stdenv.mkDerivation rec {
    name = "tezos-client-babylonnet-${babylonnet.rev}";
    phases = "copyPhase";
    copyPhase = ''
      mkdir -p $out
      cp ${binary-babylonnet} $out/${name}
    '';
  };
  tezos-license = stdenv.mkDerivation rec {
    name = "LICENSE";
    phases = "copyPhase";
    copyPhase = ''
      mkdir -p $out
      cp ${licenseFile} $out/${name}
    '';
  };

in rec {
  inherit
    mainnet-rpm-package babylonnet-rpm-package babylonnet-deb-package tezos-license
    tezos-static-mainnet tezos-static-babylonnet;
}
