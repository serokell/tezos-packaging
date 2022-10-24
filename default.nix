# SPDX-FileCopyrightText: 2022 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

let
  inherit (import
  (
    let lock = builtins.fromJSON (builtins.readFile ./flake.lock); in
    fetchTarball {
      url = "https://github.com/edolstra/flake-compat/archive/${lock.nodes.flake-compat.locked.rev}.tar.gz";
      sha256 = lock.nodes.flake-compat.locked.narHash;
    }
  ) { src = ./.; })
  defaultNix;
  pkgs = defaultNix.legacyPackages.${__currentSystem};
in with pkgs.lib; recursiveUpdate defaultNix (attrsets.mapAttrs (_: val: val.${__currentSystem}) defaultNix)
