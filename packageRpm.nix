# SPDX-FileCopyrightText: 2019 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: MPL-2.0
{ stdenv, writeTextFile, gnutar }:
pkgDesc:

let
  project = pkgDesc.project;
  version = pkgDesc.version;
  revision = pkgDesc.gitRevision;
  arch = pkgDesc.arch;
  bin = pkgDesc.bin;
  pkgName = "${project}-${version}-${revision}.${arch}";
  licenseFile = pkgDesc.licenseFile;
  src = ./.;

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
        mkdir SOURCES
        cp ${writeSpecFile} SPECS/${project}.spec
        cp ${sourceArchive} SOURCES/${sourceArchive.name}
        ls SOURCES
        mkdir -p BUILD/${project}
        cp ${licenseFile} BUILD/${project}/LICENSE

        rpmbuild -ba SPECS/${project}.spec
        cp SRPMS/${project}-${version}-${revision}.src.rpm $out
        cp RPMS/${arch}/* $out
      '';

    };
}
