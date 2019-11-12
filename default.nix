# SPDX-FileCopyrightText: 2019 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: MPL-2.0
{ pkgs ? import <nixpkgs> { } }:
with pkgs;

let
  root = ./.;
  tezos-client-static = import ./nix/static.nix;
  tezos-client-binary = "${tezos-client-static}/bin/tezos-client";
  packageDesc = {
    project = "tezos-client";
    majorVersion = "1";
    minorVersion = "0";
    packageRevision = "0";
    bin = tezos-client-binary;
    arch = "amd64";
    license = "MPL-2.0";
    dependencies = "";
    maintainer = "Serokell https://serokell.io";
    licenseFile = "${root}/LICENSES/MPL-2.0.txt";
    description = "CLI client for interacting with tezos blockchain";
  };
  buildDeb =
    import ./packageDeb.nix { inherit stdenv writeTextFile; } packageDesc;
  buildRpm = import ./packageRpm.nix { inherit stdenv writeTextFile; }
    (packageDesc // { arch = "x86_64"; });

  inherit (vmTools)
    makeImageFromDebDist makeImageFromRPMDist debDistros rpmDistros
    runInLinuxImage;
  ubuntuImage = makeImageFromDebDist debDistros.ubuntu1804x86_64;
  fedoraImage = makeImageFromRPMDist rpmDistros.fedora27x86_64;
  tezos-client-rpm-package =
    runInLinuxImage (buildRpm.packageRpm // { diskImage = fedoraImage; });

  tezos-client-deb-package =
    runInLinuxImage (buildDeb.packageDeb // { diskImage = ubuntuImage; });

in rec {
  inherit tezos-client-static tezos-client-rpm-package tezos-client-deb-package;

}
