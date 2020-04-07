# SPDX-FileCopyrightText: 2019 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: MPL-2.0
{ stdenv, writeTextFile, writeScript, runCommand, vmTools, lib, meta }:
pkg:

let
  project = lib.toLower pkg.meta.name;
  version = meta.version;
  revision = meta.gitRevision;
  pkgArch = meta.arch;
  pkgName = "${project}_0ubuntu${version}-${revision}_${pkgArch}";
  inherit (vmTools)
    makeImageFromDebDist commonDebPackages debDistros runInLinuxImage;
  ubuntuImage = makeImageFromDebDist (debDistros.ubuntu1804x86_64 // {
    packages = commonDebPackages
      ++ [ "diffutils" "libc-bin" "build-essential" "debhelper" ];
  });
  writeControlFile = writeTextFile {
    name = "control";
    text = ''
      Source: ${project}
      Section: utils
      Priority: optional
      Maintainer: Serokell <hi@serokell.io>
      Build-Depends: debhelper (>=9)
      Standards-Version: 3.9.7
      Homepage: https://gitlab.com/tezos/tezos/
      #Vcs-Git: git@gitlab.com:tezos/tezos.git
      #Vcs-Browser: https://gitlab.com/tezos/tezos.git

      Package: ${project}
      Architecture: ${meta.arch}
      Depends: ${meta.dependencies}
      Description: ${project}
       ${pkg.meta.description}
    '';
  };

  writeChangelogFile = writeTextFile {
    name = "changelog";
    text = ''
      ${project} (0ubuntu${version}-${revision}) ${meta.ubuntuVersion}; urgency=medium

        * Publish ${revision} revision of ${project}.

       -- ${meta.builderInfo} ${meta.date}
    '';
  };

  root = ./.;
  writeMakefile = writeTextFile {
    name = "Makefile";
    text = ''
      BINDIR=/usr/bin
      all:

      install:
      	mkdir -p $(DESTDIR)$(BINDIR)
      	cp ${project} $(DESTDIR)$(BINDIR)
    '';
  };

  writeRulesFile = writeScript "rules" ''
    #!/usr/bin/make -f
    %:
    	dh $@
    override_dh_strip:
  '';
  buildSourceDeb =
    runCommand "build_source_deb" { SOURCE_DATE_EPOCH = 1576846270; } ''
      mkdir -p ${project}/debian/source
      cd ${project}
      cp ${writeMakefile} Makefile
      cp ${pkg}/bin/* .
      cp ${writeControlFile} debian/control
      cp ${writeChangelogFile} debian/changelog
      cp ${meta.licenseFile} debian/copyright
      echo 9 > debian/compat
      echo "The Debian Package tezos-client-mainnet" > debian/README
      echo "3.0 (native)" > debian/source/format
      cp ${writeRulesFile} debian/rules
      dpkg-buildpackage -S -us -uc | tee ../${project}_0ubuntu${version}-${revision}_source.buildinfo 2>&1
      mkdir -p $out
      cp ../*.* $out/
    '';
in runInLinuxImage (buildSourceDeb // { diskImage = ubuntuImage; })
