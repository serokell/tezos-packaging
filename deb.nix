# SPDX-FileCopyrightText: 2019 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: MPL-2.0
{ stdenv, writeTextFile, dpkg, meta }:
pkg:
let
  project = pkg.meta.name;
  version = meta.version;
  revision = meta.gitRevision;
  pkgArch = meta.arch;
  pkgName = "${project}_0ubuntu${version}-${revision}_${pkgArch}";

  writeControlFile = writeTextFile {
    name = "control";
    text = ''
      Package: ${project}
      Version: ${version}-${revision}
      Priority: optional
      Architecture: ${meta.arch}
      Depends: ${meta.dependencies}
      Maintainer: ${meta.maintainer}
      Description: ${project}
       ${pkg.meta.description}
       Supports ${pkg.meta.supports}
    '';
  };

in stdenv.mkDerivation rec {
  name = "${pkgName}.deb";

  nativeBuildInputs = [ dpkg ];

  phases = "packagePhase";

  packagePhase = ''
    mkdir ${pkgName}
    mkdir -p ${pkgName}/usr/local/bin
    cp ${pkg}/bin/* ${pkgName}/usr/local/bin

    mkdir ${pkgName}/DEBIAN
    cp ${writeControlFile} ${pkgName}/DEBIAN/control

    dpkg-deb --build ${pkgName}
    mkdir -p $out
    cp ${name} $out/
  '';
}
