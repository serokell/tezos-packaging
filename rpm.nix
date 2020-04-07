# SPDX-FileCopyrightText: 2019 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: MPL-2.0
{ stdenv, writeTextFile, gnutar, rpm, buildFHSUserEnv
, buildSourcePackage ? false, meta }:
pkg:

let
  project = pkg.meta.name;
  version = meta.version;
  revision = meta.gitRevision;
  arch = meta.arch;
  pkgName = "${project}-${version}-${revision}.${arch}";
  licenseFile = meta.licenseFile;

  rpmbuild-env = buildFHSUserEnv {
    name = "rpmbuild-env";
    multiPkgs = pkgs: [ rpm ];
    runScript = "rpmbuild";
  };

  writeSpecFile = writeTextFile {
    name = "${project}.spec";
    text = ''
      %define debug_package %{nil}
      # %define _unpackaged_files_terminate_build 0
      Name:    ${project}
      Version: ${version}
      Release: ${revision}
      Summary: ${pkg.meta.description}
      License: ${meta.license}
      BuildArch: ${arch}
      Source0: ${project}-${version}.tar.gz
      Source1: https://gitlab.com/tezos/tezos/tree/${meta.branchName}/
      %description
      ${pkg.meta.description}
      Maintainer: ${meta.maintainer}
      %prep
      %setup -q
      %build
      %install
      mkdir -p %{buildroot}/%{_bindir}
      install -m 0755 * %{buildroot}/%{_bindir}
      %files
      %license LICENSE
      %{_bindir}/*
    '';
  };

  sourceArchive = stdenv.mkDerivation rec {
    name = "${project}-${version}.tar.gz";

    phases = "archivePhase";

    archivePhase = ''
      mkdir ${project}-${version}
      cp ${licenseFile} ${project}-${version}/LICENSE
      cp ${pkg}/bin/* ${project}-${version}/
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
