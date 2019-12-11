# SPDX-FileCopyrightText: 2019 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: MPL-2.0
{ stdenv, writeTextFile, rpm, buildFHSUserEnv }:
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
    '';
  };

  rpmbuild-env = buildFHSUserEnv {
    name = "rpmbuild-env";
    multiPkgs = pkgs: [ rpm ];
    runScript = "rpmbuild";
  };

in stdenv.mkDerivation rec {
  name = "${pkgName}";

  phases = "packagePhase";
  buildInputs = [ rpmbuild-env ];
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

    rpmbuild-env -bb SPECS/${project}.spec --dbpath $HOME
    mkdir -p $out
    cp RPMS/*/*.rpm $out/
  '';

}
