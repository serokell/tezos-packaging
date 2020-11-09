# SPDX-FileCopyrightText: 2020 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ

# zcash-params required for building some of the tezos binaries
# and for running tests
{ pkgs ? import ./pkgs.nix {}}:
with pkgs;
let
  sapling-spend-params = fetchurl {
    url = "https://download.z.cash/downloads/sapling-spend.params";
    sha256 = "04zwgrkpb6x782x9d05p0id2hccw5prh94jqqpcmyfmv7b9gyj4f";
  };
  sapling-output-params = fetchurl {
    url = "https://download.z.cash/downloads/sapling-output.params";
    sha256 = "1r5h7wzhwmw8vcww74b1vr6ynacwm3myg5x3jpzcy2xvp75vn3ig";
  };
  sprout-groth-16-params = fetchurl {
    url = "https://download.z.cash/downloads/sprout-groth16.params";
    sha256 = "0l2vwl7bz9a8yhmbfrdji2vj5iw4qk3wi2g5pn7lja03qq0dg1dn";
  };
in stdenv.mkDerivation {
  name = "zcash-params";
  phases = [ "installPhase" ];
  installPhase = ''
    mkdir -p $out/zcash-params/
    cp ${sapling-spend-params} $out/zcash-params/sapling-spend.params
    cp ${sapling-output-params} $out/zcash-params/sapling-output.params
    cp ${sprout-groth-16-params} $out/zcash-params/sprout-groth16.params
  '';
}
