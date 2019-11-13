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
  arch = pkgDesc.arch;
  bin = pkgDesc.bin;
  pkgName = "${project}-${majorVersion}.${minorVersion}-${pkgRevision}.${arch}";
  licenseFile = pkgDesc.licenseFile;

  writeSpecFile = writeTextFile {
    name = "${project}.spec";
    text = ''
      Name:    ${project}
      Release: ${pkgRevision}
      Summary: ${pkgDesc.description}
      License: ${pkgDesc.license}
      Version: ${majorVersion}.${minorVersion}

      %description
      ${pkgDesc.description}

      %files
      /usr/local/bin/${project}
      %doc %name-%version/LICENSE
    '';
  };

in rec {
  packageRpm =
    stdenv.mkDerivation {
      name = "${pkgName}.rpm";

      phases = "packagePhase";

      packagePhase = ''
        HOME=$PWD
        mkdir rpmbuild
        cd rpmbuild
        mkdir SPECS
        cp ${writeSpecFile} SPECS/${project}.spec
        mkdir -p BUILD/${project}-${majorVersion}.${minorVersion}
        cp ${licenseFile} BUILD/${project}-${majorVersion}.${minorVersion}/LICENSE

        mkdir -p BUILDROOT/${pkgName}/usr/local/bin
        cp ${bin} BUILDROOT/${pkgName}/usr/local/bin/${project}

        rpmbuild -bb SPECS/${project}.spec
        cp RPMS/${arch}/${pkgName}.rpm $out
      '';

    };
}
