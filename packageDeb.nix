# SPDX-FileCopyrightText: 2019 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: MPL-2.0
{ stdenv, writeTextFile }:
pkgDesc:

let
  project = pkgDesc.project;
  majorVersion = pkgDesc.majorVersion;
  minorVersion = pkgDesc.minorVersion;
  pkgRevision = pkgDesc.packageRevision;
  bin = pkgDesc.bin;
  pkgName = "${project}_${majorVersion}.${minorVersion}-${pkgRevision}";

  writeControlFile = writeTextFile {
    name = "control";
    text = ''
      Package: ${project}
      Version: ${majorVersion}.${minorVersion}-${pkgRevision}
      Priority: optional
      Architecture: ${pkgDesc.arch}
      Depends: ${pkgDesc.dependencies}
      Maintainer: ${pkgDesc.maintainer}
      Description: ${project}
       ${pkgDesc.description}
    '';
  };

in rec {
  packageDeb =
    stdenv.mkDerivation {
      name = "${pkgName}.deb";

      phases = "packagePhase";

      packagePhase = ''
        mkdir ${pkgName}
        mkdir -p ${pkgName}/usr/local/bin
        cp ${bin} ${pkgName}/usr/local/bin/${project}

        mkdir ${pkgName}/DEBIAN
        cp ${writeControlFile} ${pkgName}/DEBIAN/control

        dpkg-deb --build ${pkgName}
        mv ${pkgName}.deb $out
      '';
    };
}
