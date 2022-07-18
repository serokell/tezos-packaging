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
in defaultNix // defaultNix.devShells.${__currentSystem}
             // { binaries-test = defaultNix.binaries-test.${__currentSystem};
                  release = defaultNix.release.${__currentSystem};
                }
