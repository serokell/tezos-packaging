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
  binaries = builtins.listToAttrs (map (meta: {
    inherit (meta) name;
    value = bin pkgs.pkgsMusl.ocamlPackages.${meta.name} // { inherit meta; };
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

  release =
    pkgs.callPackage ./release.nix { inherit source bundled timestamp; };

  test-binaries = pkgs.runCommand "test-binaries" { } ''
    for f in ${bundled.binaries}/bin/*; do
      echo "$f"
      "$f" --help &> /dev/null
    done
    # Test that tezos-node run works for carthagenet
    ${bundled.binaries}/bin/tezos-node config init --data-dir node-dir --network carthagenet
    ${bundled.binaries}/bin/tezos-node identity generate 1 --data-dir node-dir
    timeout --preserve-status 5 ${bundled.binaries}/bin/tezos-node run --data-dir node-dir --network carthagenet
    rm -rf node-dir
    # Test that tezos-node run works for mainnet
    ${bundled.binaries}/bin/tezos-node config init --data-dir node-dir --network mainnet
    ${bundled.binaries}/bin/tezos-node identity generate 1 --data-dir node-dir
    timeout --preserve-status 5 ${bundled.binaries}/bin/tezos-node run --data-dir node-dir --network mainnet
    touch $out
  '';

in bundled // rec { inherit test-binaries release; }
