# SPDX-FileCopyrightText: 2019 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: MPL-2.0
{ stdenv, writeTextFile, gnutar, rpm, buildFHSUserEnv
, buildSourcePackage ? false }:
pkgDesc:

let
  project = pkgDesc.project;
  version = pkgDesc.version;
  revision = pkgDesc.gitRevision;
  arch = pkgDesc.arch;
  bin = pkgDesc.bin;
  pkgName = "${project}-${version}-${revision}.${arch}";
  licenseFile = pkgDesc.licenseFile;

  rpmbuild-env = buildFHSUserEnv {
    name = "rpmbuild-env";
    multiPkgs = pkgs: [ rpm ];
    runScript = "rpmbuild";
  };

  writeSpecFile = writeTextFile {
    name = "${project}.spec";
    text = ''
      %define debug_package %{nil}
      %define _unpackaged_files_terminate_build 0
      Name:    ${project}
      Version: ${version}
      Release: ${revision}
      Summary: ${pkgDesc.description}
      License: ${pkgDesc.license}
      BuildArch: ${arch}
      Source0: ${project}-${version}.tar.gz
      Source1: https://gitlab.com/tezos/tezos/tree/${pkgDesc.branchName}/
      %description
      ${pkgDesc.description}
      Maintainer: ${pkgDesc.maintainer}
      %prep
      %setup -q
      %build
      %install
      mkdir -p %{buildroot}/%{_bindir}
      install -m 0755 %{name} %{buildroot}/%{_bindir}/%{name}
      %files
      %license LICENSE
      %{_bindir}/%{name}
    '';
  };

  sourceArchive = stdenv.mkDerivation rec {
    name = "${project}-${version}.tar.gz";

    phases = "archivePhase";

    archivePhase = ''
      mkdir ${project}-${version}
      cp ${licenseFile} ${project}-${version}/LICENSE
      cp ${bin} ${project}-${version}/${project}
      tar -cvzf ${name} ${project}-${version}
      cp ${name} $out
    '';
  };

in stdenv.mkDerivation rec {
  rpmBuildFlag = if buildSourcePackage then "-bs" else "-bb";
  name = "${pkgName}.rpm";

  phases = "packagePhase";

  buildInputs = [ rpmbuild-env ];

  packagePhase = ''
    HOME=$PWD
    mkdir rpmbuild
    cd rpmbuild
    mkdir SPECS
    mkdir SOURCES
    cp ${writeSpecFile} SPECS/${project}.spec
    cp ${sourceArchive} SOURCES/${sourceArchive.name}
    mkdir -p BUILD/${project}
    cp ${licenseFile} BUILD/${project}/LICENSE
    rpmbuild-env ${rpmBuildFlag} SPECS/${project}.spec --define '_bindir /usr/bin' --define '_datadir /usr/share'
    mkdir -p $out
    ${if buildSourcePackage then "cp SRPMS/*.src.rpm $out/" else "cp RPMS/*/*.rpm $out/"}
  '';

}
