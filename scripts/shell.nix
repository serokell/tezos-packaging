# SPDX-FileCopyrightText: 2019-2020 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: MPL-2.0

let
  overlays =
    [
      (self: super: {
        gh = (super.callPackage "${super.path}/pkgs/applications/version-management/git-and-tools/gh" {
          buildGoModule = args: super.buildGoModule (args // rec {
            version = "1.2.0";
            vendorSha256 = "0ybbwbw4vdsxdq4w75s1i0dqad844sfgs69b3vlscwfm6g3i9h51";
            src = self.fetchFromGitHub {
              owner = "cli";
              repo = "cli";
              rev = "v${version}";
              sha256 = "17hbgi1jh4p07r4p5mr7w7p01i6zzr28mn5i4jaki7p0jwfqbvvi";
            };
          });
        });
      })
    ];
in

{ pkgs ? import (import ../nix/nix/sources.nix {}).nixpkgs { inherit overlays; } }:
with pkgs;
mkShell {
  buildInputs = [ gh git rename ];
}
