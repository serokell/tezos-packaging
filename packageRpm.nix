# SPDX-FileCopyrightText: 2019 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: MPL-2.0
{ stdenv, writeTextFile }:
pkgDesc:

let
  project = pkgDesc.project;
  version = pkgDesc.version;
  revision = pkgDesc.gitRevision;
  arch = pkgDesc.arch;
  bin = pkgDesc.bin;
  pkgName = "${project}-${version}-${revision}.${arch}";
  licenseFile = pkgDesc.licenseFile;

  writeSpecFile = writeTextFile {
    name = "${project}.spec";
    text = ''
      Name:    ${project}
      Version: ${version}
      Release: ${revision}
      Summary: ${pkgDesc.description}
      License: ${pkgDesc.license}

      %description
      ${pkgDesc.description}
      Maintainer: ${pkgDesc.maintainer}

      %files
      /usr/local/bin/${project}
      %doc %name/LICENSE
    '';
  };

in rec {
  packageRpm =
    stdenv.mkDerivation rec {
      name = "${pkgName}.rpm";

      phases = "packagePhase";

      packagePhase = ''
        HOME=$PWD
        mkdir rpmbuild
        cd rpmbuild
        mkdir SPECS
        cp ${writeSpecFile} SPECS/${project}.spec
        mkdir -p BUILD/${project}
        cp ${licenseFile} BUILD/${project}/LICENSE

        mkdir -p BUILDROOT/${pkgName}/usr/local/bin
        cp ${bin} BUILDROOT/${pkgName}/usr/local/bin/${project}

        rpmbuild -bb SPECS/${project}.spec
        cp RPMS/${arch}/${pkgName}.rpm $out
      '';

    };
}
