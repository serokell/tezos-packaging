# SPDX-FileCopyrightText: 2019 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: MPL-2.0

{ writeTextDir, runCommand, buildEnv, timestamp, bundled, source }:
let
  protocols = import ./protocols.nix;
  release-binaries = import ./release-binaries.nix;
  release-notes = writeTextDir "release-notes.md" ''
    Automatic release on ${builtins.substring 0 8 timestamp}

    This release contains assets based on [${source.ref} release](https://gitlab.com/tezos/tezos/tree/${source.ref}).

    Binaries without protocol suffixes support the following protocols (unsupported protocols are listed for reference):
    ${builtins.concatStringsSep "\n" (map (x: "- [ ] `${x}`") protocols.ignored
      ++ map (x: "- [x] `${x}`") (protocols.allowed ++ protocols.active))}

    Descriptions for binaries included in this release:
    ${builtins.concatStringsSep "\n"
    (map ({ name, description, ... }: "- `${name}`: ${description}")
      release-binaries)}
  '';
  releaseNoTarball = buildEnv {
    name = "tezos-release-no-tarball";
    paths = [ "${bundled.binaries}/bin" LICENSE release-notes ];
  };
  tarballName = "binaries-${builtins.replaceStrings ["v"] [""] source.ref}-1.tar.gz";
  binariesTarball = runCommand "binaries-tarball" { }
    "mkdir $out; tar --owner=serokell:1000 --mode='u+rwX' -czhf $out/${tarballName} -C ${bundled.binaries}/bin .";
  LICENSE = writeTextDir "LICENSE" (builtins.readFile "${source}/LICENSE");
in buildEnv {
  name = "tezos-release";
  paths = [ releaseNoTarball binariesTarball ];
}
