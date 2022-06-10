# SPDX-FileCopyrightText: 2019 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ

{ sources, pkgs, protocols, patches ? [ ], ... }:
let
  source = sources.tezos;
  release-binaries = builtins.filter (elem: elem.name != "tezos-sandbox")
    (import ./build/release-binaries.nix protocols);
  binaries = builtins.listToAttrs (map (meta: {
    inherit (meta) name;
    value = pkgs.tezosPackages.${meta.name} // { inherit meta; };
  }) release-binaries);

  # Bundle the contents of a package set together, leaving the original attrs intact
  bundle = name: pkgSet:
    pkgSet // (pkgs.buildEnv {
      inherit name;
      paths = builtins.attrValues pkgSet;
    });

  artifacts = { inherit binaries; };
  bundled = (builtins.mapAttrs bundle artifacts);

in (d: with builtins;
     listToAttrs (map (drv:
       { name = drv; value = d.${drv}; }
     ) (filter (name: substring 0 5 name == "tezos") (attrNames d)))
   ) bundled.binaries // { inherit (bundled) binaries; }
