# SPDX-FileCopyrightText: 2019 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: MPL-2.0

{ timestamp ? "19700101", patches ? [ ], date ? "Thu, 1 Jan 1970 10:00:00 +0300"
, builderInfo ? "", ubuntuVersion ? "bionic" }:
let
  pkgs = import ./pkgs.nix { };
  source = (import ./nix/sources.nix).tezos;
  protocols = import ./protocols.nix;
  bin = pkgs.callPackage ./bin.nix { };
  release-binaries = import ./release-binaries.nix;
  binaries = builtins.listToAttrs (map ({ name, ... }@meta: {
    inherit name;
    value = bin pkgs.pkgsMusl.ocamlPackages.${name} // { inherit meta; };
  }) release-binaries);
  commonMeta = {
    gitRevision = source.rev;
    version = toString timestamp;
    license = "MPL-2.0";
    dependencies = "";
    maintainer = "Serokell https://serokell.io";
    branchName = source.ref;
    licenseFile = "${source}/LICENSE";
  };
  rpmMeta = { arch = "x86_64"; };
  debMeta = {
    arch = "amd64";
    inherit builderInfo ubuntuVersion date;
  };
  deb = builtins.mapAttrs
    (_: pkgs.callPackage ./deb.nix { meta = commonMeta // debMeta; }) binaries;
  rpm = builtins.mapAttrs
    (_: pkgs.callPackage ./rpm.nix { meta = commonMeta // rpmMeta; }) binaries;
  debSource = builtins.mapAttrs
    (_: pkgs.callPackage ./debSource.nix { meta = commonMeta // debMeta; })
    binaries;
  rpmSource = builtins.mapAttrs (_:
    pkgs.callPackage ./rpm.nix {
      meta = commonMeta // rpmMeta;
      buildSourcePackage = true;
    }) binaries;

  # Bundle the contents of a package set together, leaving the original attrs intact
  bundle = name: pkgSet:
    pkgSet // (pkgs.buildEnv {
      inherit name;
      paths = builtins.attrValues pkgSet;
    });

  artifacts = { inherit binaries deb rpm debSource rpmSource; };
  bundled = builtins.mapAttrs bundle artifacts;
  release-notes = pkgs.writeTextDir "release-notes.md" ''
    Automatic release on ${builtins.substring 0 8 timestamp}

    This release contains assets based on [revision ${source.rev}](https://gitlab.com/tezos/tezos/tree/${source.rev}) of ${source.ref} branch.

    This release targets the following protocols (ignored protocols are listed for reference):
    ${builtins.concatStringsSep "\n" (map (x: "- [ ] `${x}`") protocols.ignored
      ++ map (x: "- [x] `${x}`") (protocols.allowed ++ protocols.active))}

    <!--
    When making a new release, replace `auto-release` with actual release tag:
    -->
    For more information about release assets see [README section](https://github.com/serokell/tezos-packaging/blob/auto-release/README.md#obtain-binaries-or-packages-from-github-release).
  '';
  LICENSE = pkgs.writeTextDir "LICENSE" (builtins.readFile "${source}/LICENSE");

  test-binaries = pkgs.runCommand "test-binaries" { } ''
    for f in ${bundled.binaries}/bin/*; do
      echo "$f"
      "$f" --help &> /dev/null
    done
    touch $out
  '';
  releaseNoTarball = pkgs.buildEnv {
    name = "tezos-release";
    paths = [ "${bundled.binaries}/bin" LICENSE release-notes ];
  };
  releaseTarball = pkgs.runCommand "release-tarball" { }
    "mkdir $out; tar --owner=serokell:1000 --mode='u+rwX' -czhf $out/release.tar.gz -C ${releaseNoTarball} .";

in bundled // rec {
  inherit test-binaries;
  release = pkgs.buildEnv {
    name = "tezos-release";
    paths = [ releaseNoTarball releaseTarball ];
  };
}
