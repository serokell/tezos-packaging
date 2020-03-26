# SPDX-FileCopyrightText: 2019 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: MPL-2.0
{ pkgs ? import <nixpkgs> { }, timestamp ? "19700101", patches ? [ ]
, date ? "Thu, 1 Jan 1970 10:00:00 +0300", builderInfo ? ""
, ubuntuVersion ? "bionic" }:
with pkgs;

let
  root = ./.;
  protocol005 = rec {
    protocolName = "005_PsBabyM1";
    binarySuffix = builtins.replaceStrings [ "_" ] [ "-" ] protocolName;
  };
  protocol006 = rec {
    protocolName = "006_PsCARTHA";
    binarySuffix = builtins.replaceStrings [ "_" ] [ "-" ] protocolName;
  };
  protocols = [ protocol005 protocol006 ];
  master = {
    rev = "60b977cd";
    sha256 = "1v9v5z5i3cs9jw48m3xx9w4fqkns37nn464fr7hds7wgmwfmf1sp";
    patches = [ ./nix/fix-master.patch ] ++ patches;
    inherit protocols;
  };
  static-nix = import ./nix/static.nix;
  tezos-static-master = static-nix master;

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

  binaries =
    packDirectory "binaries-${master.rev}" "${tezos-static-master}/bin";
  licenseFile = "${tezos-static-master}/LICENSE";

  mkPackageDesc = { executableName, binPath, description }@executableDesc:
    let
      packageDesc = {
        inherit description licenseFile;
        bin = "${tezos-static-master}/${binPath}";
        gitRevision = master.rev;
        project = "${executableName}";
        version = toString timestamp;
        arch = "amd64";
        license = "MPL-2.0";
        dependencies = "";
        maintainer = "Serokell https://serokell.io";
        branchName = "master";
      };
    in packageDesc;

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
      executableName = "tezos-signer";
      binPath = "/bin/tezos-signer";
      description = "A client to remotely sign operations or blocks";
    }
  ] ++ lib.flatten (map (protocol: [
    {
      executableName = "tezos-baker-${protocol.binarySuffix}";
      binPath = "/bin/tezos-baker-${protocol.binarySuffix}";
      description = "Daemon for baking";
    }
    {
      executableName = "tezos-accuser-${protocol.binarySuffix}";
      binPath = "/bin/tezos-accuser-${protocol.binarySuffix}";
      description = "Daemon for accusing";
    }
    {
      executableName = "tezos-endorser-${protocol.binarySuffix}";
      binPath = "/bin/tezos-endorser-${protocol.binarySuffix}";
      description = "Daemon for endorsing";
    }
  ]) protocols);

  tezos-license = stdenv.mkDerivation rec {
    name = "LICENSE";
    phases = "copyPhase";
    copyPhase = ''
      mkdir -p $out
      cp ${licenseFile} $out/${name}
    '';
  };

  packageDescs = map mkPackageDesc tezos-executables;

  buildDeb = import ./packageDeb.nix { inherit stdenv writeTextFile dpkg; };
  buildRpm = packageDesc:
    import ./packageRpm.nix {
      inherit stdenv writeTextFile gnutar rpm buildFHSUserEnv;
    } (packageDesc // { arch = "x86_64"; });
  buildSourceDeb = packageDesc:
    import ./packageSourceDeb.nix {
      inherit stdenv writeTextFile writeScript runCommand;
      inherit (lib) toLower;
    } packageDesc { inherit date builderInfo ubuntuVersion; };
  buildSourceRpm = packageDesc:
    import ./packageRpm.nix {
      inherit stdenv writeTextFile gnutar rpm buildFHSUserEnv;
      buildSourcePackage = true;
    } (packageDesc // { arch = "x86_64"; });

  moveDerivations = drvs:
    runCommand "move_derivations" { inherit drvs; } ''
      mkdir -p $out
      for drv in $drvs; do
        ln -s $drv/* $out
      done
    '';

  deb-packages = moveDerivations (map buildDeb packageDescs);
  rpm-packages = moveDerivations (map buildRpm packageDescs);

  inherit (vmTools)
    makeImageFromDebDist commonDebPackages debDistros runInLinuxImage;
  ubuntuImage = makeImageFromDebDist (debDistros.ubuntu1804x86_64 // {
    packages = commonDebPackages
      ++ [ "diffutils" "libc-bin" "build-essential" "debhelper" ];
  });
  buildSourceDebInVM = pkgDesc:
    runInLinuxImage ((buildSourceDeb pkgDesc) // { diskImage = ubuntuImage; });

  deb-source-packages = moveDerivations (map buildSourceDebInVM packageDescs);

  rpm-source-packages = moveDerivations (map buildSourceRpm packageDescs);

  releaseFile = writeTextFile {
    name = "release-notes.md";
    text = ''
      Automatic release on ${builtins.substring 0 8 timestamp}

      This release contains assets based on [${master.rev} revision](https://gitlab.com/tezos/tezos/tree/${master.rev}) of master branch.
      <!--
      When making a new release, replace `auto-release` with actual release tag:
      -->
      For more information about release assets see [README section](https://github.com/serokell/tezos-packaging/blob/auto-release/README.md#obtain-binaries-or-packages-from-github-release).
    '';
  };
  releaseNotes = runCommand "release-notes" { } ''
    mkdir -p $out
    cp ${releaseFile} $out/
  '';

  test-binaries = runCommand "test-binaries" { inherit tezos-static-master; } ''
    for f in ${tezos-static-master}/bin/*; do
      echo "$f"
      "$f" --help &> /dev/null
    done
    mkdir -p $out
  '';

in rec {
  inherit deb-packages deb-source-packages rpm-source-packages rpm-packages
    binaries tezos-license releaseNotes test-binaries;
    binaries-drv = tezos-static-master;
}
