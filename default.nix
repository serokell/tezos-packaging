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
    protoName = "005_PsBabyM1";
    binarySuffix = "005-PsBabyM1";
  };
  babylonnet = {
    rev = "b8731913";
    sha256 = "1pakf1s6bg76fq42mb8fj1immz9g9wwimd522cpx8k28zf0hkl5i";
    patchFile = ./nix/fix-babylonnet.patch;
    protoName = "005_PsBabyM1";
    binarySuffix = "005-PsBabyM1";
  };
  tezos-static-mainnet = import ./nix/static.nix mainnet;
  tezos-static-babylonnet = import ./nix/static.nix babylonnet;

  packDirectory = archiveName: pathToPack:
    stdenv.mkDerivation rec {
      name = "${archiveName}.tar.gz";
      phases = "archivePhase";
      nativeBuildInputs = [ gnutar ];
      archivePhase = ''
        mkdir -p ${archiveName}
        cp -a ${pathToPack}/. ${archiveName}/
        tar -cvzf ${name} ${archiveName}
        mkdir -p $out
        cp ${name} $out/
      '';
    };

  mainnet-binaries = packDirectory "tezos-mainnet-binaries-${mainnet.rev}"
    "${tezos-static-mainnet}/bin";
  babylonnet-binaries =
    packDirectory "tezos-babylonnet-binaries-${babylonnet.rev}"
    "${tezos-static-babylonnet}/bin";

  mkPackageDescs = { executableName, binPath, description }@executableDesc:
    let
      mainnetDesc = {
        inherit description;
        bin = "${tezos-static-mainnet}/${binPath}";
        gitRevision = mainnet.rev;
        project = "${executableName}-mainnet";
        version = toString timestamp;
        arch = "amd64";
        license = "MPL-2.0";
        dependencies = "";
        maintainer = "Serokell https://serokell.io";
        licenseFile = "${root}/LICENSES/MPL-2.0.txt";
        branchName = "mainnet";
      };
      babylonnetDesc = mainnetDesc // {
        bin = "${tezos-static-babylonnet}/${binPath}";
        project = "${executableName}-babylonnet";
        gitRevision = babylonnet.rev;
        branchName = "babylonnet";
      };
    in [ mainnetDesc babylonnetDesc ];

  tezos-executables = [
    { executableName = "tezos-client";
      binPath = "/bin/tezos-client";
      description = "CLI client for interacting with tezos blockchain";
    }
    { executableName = "tezos-client-admin";
      binPath = "/bin/tezos-client-admin";
      description = "Administration tool for the node";
    }
    { executableName = "tezos-node";
      binPath = "/bin/tezos-client";
      description =
        "Entry point for initializing, configuring and running a Tezos node";
    }
    { executableName = "tezos-baker";
      binPath = "/bin/tezos-baker-${mainnet.binarySuffix}";
      description = "Daemon for baking";
    }
    { executableName = "tezos-accuser";
      binPath = "/bin/tezos-accuser-${mainnet.binarySuffix}";
      description = "Daemon for accusing";
    }
    { executableName = "tezos-endorser";
      binPath = "/bin/tezos-endorser-${mainnet.binarySuffix}";
      description = "Daemon for endorsing";
    }
    { executableName = "tezos-signer";
      binPath = "/bin/tezos-signer";
      description = "A client to remotely sign operations or blocks";
    }
  ];

  packageDescs = lib.flatten (map mkPackageDescs tezos-executables);

  buildDeb = import ./packageDeb.nix { inherit stdenv writeTextFile dpkg; };
  buildRpm = packageDesc:
    import ./packageRpm.nix {
      inherit stdenv writeTextFile gnutar rpm buildFHSUserEnv;
    } (packageDesc // { arch = "x86_64"; });

  moveDerivations = name: drvs:
    stdenv.mkDerivation rec {
      inherit name drvs;

      buildCommand = ''
        mkdir -p ${name}
        backup=$PWD
        for drv in $drvs; do
          cd $drv
          cp * $backup/${name}/
        done
        cd $backup
        mkdir -p $out
        cp ${name}/* $out
      '';
    };

  deb-packages = moveDerivations "deb-packages" (map buildDeb packageDescs);

  rpm-packages = moveDerivations "rpm-packages" (map buildRpm packageDescs);

in rec { inherit deb-packages rpm-packages mainnet-binaries babylonnet-binaries; }
