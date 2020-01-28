# SPDX-FileCopyrightText: 2019 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: MPL-2.0
{ pkgs ? import <nixpkgs> { }, timestamp ? "19700101" }:
with pkgs;

let
  root = ./.;
  protocol005 = rec {
    protocolName = "005_PsBabyM1";
    binarySuffix = builtins.replaceStrings [ "_" ] [ "-" ] protocolName;
  };
  mainnet = {
    rev = "94f779a7";
    sha256 = "16lxilng5q8fr2ll6h4hf7wlvac6nmw4cx10cbgzj5ks090bl97r";
    patchFile = ./nix/fix-mainnet.patch;
    protocol = protocol005;
  };
  babylonnet = {
    rev = "b8731913";
    sha256 = "1pakf1s6bg76fq42mb8fj1immz9g9wwimd522cpx8k28zf0hkl5i";
    patchFile = ./nix/fix-babylonnet.patch;
    protocol = protocol005;
  };
  static-nix = import ./nix/static.nix;
  tezos-static-mainnet = static-nix mainnet;
  tezos-static-babylonnet = static-nix babylonnet;

  packDirectory = archiveName: pathToPack:
    stdenv.mkDerivation rec {
      name = "${archiveName}.tar.gz";
      phases = "archivePhase";
      nativeBuildInputs = [ gnutar ];
      archivePhase = ''
        mkdir -p $out
        tar -cvzf $out/${name} --mode='u+rwX' -C ${pathToPack} $(ls ${pathToPack})
      '';
    };
  mainnet-binaries = packDirectory "binaries-mainnet-${mainnet.rev}"
    "${tezos-static-mainnet}/bin";
  babylonnet-binaries = packDirectory "binaries-babylonnet-${babylonnet.rev}"
    "${tezos-static-babylonnet}/bin";
  licenseFile = "${tezos-static-mainnet}/LICENSE";

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
        licenseFile = "${tezos-static-mainnet}/LICENSE";
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
    {
      executableName = "tezos-client";
      binPath = "/bin/tezos-client";
      description = "CLI client for interacting with tezos blockchain";
    }
    {
      executableName = "tezos-admin-client";
      binPath = "/bin/tezos-admin-client";
      description = "Administration tool for the node";
    }
    {
      executableName = "tezos-node";
      binPath = "/bin/tezos-node";
      description =
        "Entry point for initializing, configuring and running a Tezos node";
    }
    {
      executableName = "tezos-baker";
      binPath = "/bin/tezos-baker-${protocol005.binarySuffix}";
      description = "Daemon for baking";
    }
    {
      executableName = "tezos-accuser";
      binPath = "/bin/tezos-accuser-${protocol005.binarySuffix}";
      description = "Daemon for accusing";
    }
    {
      executableName = "tezos-endorser";
      binPath = "/bin/tezos-endorser-${protocol005.binarySuffix}";
      description = "Daemon for endorsing";
    }
    {
      executableName = "tezos-signer";
      binPath = "/bin/tezos-signer";
      description = "A client to remotely sign operations or blocks";
    }
  ];

  tezos-license = stdenv.mkDerivation rec {
    name = "LICENSE";
    phases = "copyPhase";
    copyPhase = ''
      mkdir -p $out
      cp ${licenseFile} $out/${name}
    '';
  };

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
        mkdir -p $out
        for drv in $drvs; do
          cp $drv/* $out
        done
      '';
    };

  deb-packages = moveDerivations "deb-packages" (map buildDeb packageDescs);
  rpm-packages = moveDerivations "rpm-packages" (map buildRpm packageDescs);

  releaseFile = writeTextFile {
    name = "release-notes.md";
    text = ''
      Automatic release on ${builtins.substring 0 8 timestamp}

      This release contains assets based on [${babylonnet.rev} revision](https://gitlab.com/tezos/tezos/tree/${babylonnet.rev}) of babylonnet branch and
      [${mainnet.rev} revision](https://gitlab.com/tezos/tezos/tree/${mainnet.rev}) of mainnet branch from [tezos repository](https://gitlab.com/tezos/tezos/).
      <!--
      When making a new release, replace `auto-release` with actual release tag:
      -->
      For more information about release assets see [README section](https://github.com/serokell/tezos-packaging/blob/auto-release/README.md#obtain-binaries-or-packages-from-github-release).
    '';
  };
  releaseNotes = runCommand "release-notes" {} ''
    mkdir -p $out
    cp ${releaseFile} $out/
  '';

in rec {
  inherit deb-packages rpm-packages mainnet-binaries babylonnet-binaries
    tezos-license releaseNotes;
}
