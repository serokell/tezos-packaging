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
  };
  babylonnet = {
    rev = "b8731913";
    sha256 = "1pakf1s6bg76fq42mb8fj1immz9g9wwimd522cpx8k28zf0hkl5i";
    patchFile = ./nix/fix-babylonnet.patch;
  };
  tezos-client-static-mainnet = import ./nix/static.nix mainnet;
  tezos-client-static-babylonnet = import ./nix/static.nix babylonnet;
  binary-mainnet = "${tezos-client-static-mainnet}/bin/tezos-client";
  binary-babylonnet = "${tezos-client-static-babylonnet}/bin/tezos-client";
  packageDesc-mainnet = {
    project = "tezos-client-mainnet";
    version = toString timestamp;
    bin = binary-mainnet;
    arch = "amd64";
    license = "MPL-2.0";
    dependencies = "";
    maintainer = "Serokell https://serokell.io";
    licenseFile = "${root}/LICENSES/MPL-2.0.txt";
    description = "CLI client for interacting with tezos blockchain";
    gitRevision = mainnet.rev;
  };

  packageDesc-babylonnet = packageDesc-mainnet // {
    project = "tezos-client-babylonnet";
    bin = binary-babylonnet;
    gitRevision = babylonnet.rev;
  };

  buildDeb = import ./packageDeb.nix { inherit stdenv writeTextFile; };
  buildRpm = packageDesc:
    import ./packageRpm.nix { inherit stdenv writeTextFile gnutar; }
    (packageDesc // { arch = "x86_64"; });

  inherit (vmTools)
    makeImageFromDebDist makeImageFromRPMDist debDistros rpmDistros
    runInLinuxImage;
  ubuntuImage = makeImageFromDebDist debDistros.ubuntu1804x86_64;
  fedoraImage = makeImageFromRPMDist rpmDistros.fedora27x86_64;

  mainnet-rpm-package = runInLinuxImage
    ((buildRpm packageDesc-mainnet).packageRpm // { diskImage = fedoraImage; });

  mainnet-deb-package = runInLinuxImage
    ((buildDeb packageDesc-mainnet).packageDeb // { diskImage = ubuntuImage; });

  babylonnet-rpm-package = runInLinuxImage
    ((buildRpm packageDesc-babylonnet).packageRpm // {
      diskImage = fedoraImage;
    });

  babylonnet-deb-package = runInLinuxImage
    ((buildDeb packageDesc-babylonnet).packageDeb // {
      diskImage = ubuntuImage;
    });

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

in rec {
  inherit tezos-client-mainnet tezos-client-babylonnet mainnet-deb-package
    mainnet-rpm-package babylonnet-rpm-package babylonnet-deb-package;
}
