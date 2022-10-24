# SPDX-FileCopyrightText: 2019 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ

{ sources, pkgs, protocols, patches ? [ ], ... }:
let
  source = sources.tezos;
  release-binaries = import ./build/release-binaries.nix protocols;
in {
  octez-binaries = builtins.listToAttrs (map (meta: {
    inherit (meta) name;
    value = pkgs.octezPackages.${meta.name} // { inherit meta; };
  }) release-binaries);

  tezos-binaries = builtins.listToAttrs (map (meta:
    let
      newMeta = meta // { name = builtins.replaceStrings [ "octez" ] [ "tezos" ] meta.name; };
    in {
      inherit (newMeta) name;
      value = { inherit newMeta; } // (pkgs.octezPackages.${meta.name}.overrideAttrs (pkg: {
        inherit (newMeta) name;
        postInstall = ''
          ln -s $out/bin/${meta.name} $out/bin/${newMeta.name}
        '';
    }));
  }) release-binaries);
}
