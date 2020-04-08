# SPDX-FileCopyrightText: 2019 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: MPL-2.0

let
  protocols = import ./protocols.nix;
  release-binaries = import ./release-binaries.nix;
in { writeTextDir, runCommand, buildEnv, timestamp, bundled, source }:
let
  release-notes = writeTextDir "release-notes.md" ''
    Automatic release on ${builtins.substring 0 8 timestamp}

    This release contains assets based on [revision ${source.rev}](https://gitlab.com/tezos/tezos/tree/${source.rev}) of ${source.ref} branch.

    Binaries without protocol suffixes support the following protocols (unsupported protocols are listed for reference):
    ${builtins.concatStringsSep "\n" (map (x: "- [ ] `${x}`") protocols.ignored
      ++ map (x: "- [x] `${x}`") (protocols.allowed ++ protocols.active))}

    <!--
    When making a new release, replace `auto-release` with actual release tag:
    -->
    For more information about release assets see [README section](https://github.com/serokell/tezos-packaging/blob/auto-release/README.md#obtain-binaries-or-packages-from-github-release).
  '';
  releaseNoTarball = buildEnv {
    name = "tezos-release";
    paths = [ "${bundled.binaries}/bin" LICENSE release-notes ];
  };
  releaseTarball = runCommand "release-tarball" { }
    "mkdir $out; tar --owner=serokell:1000 --mode='u+rwX' -czhf $out/release.tar.gz -C ${releaseNoTarball} .";
  LICENSE = writeTextDir "LICENSE" (builtins.readFile "${source}/LICENSE");
in buildEnv {
  name = "tezos-release";
  paths = [ releaseNoTarball releaseTarball ];
}
