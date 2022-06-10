# SPDX-FileCopyrightText: 2020 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ

# zcash-params required for building some of the tezos binaries
# and for running tests
{ pkgs }:
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
in stdenv.mkDerivation {
  name = "zcash-params";
  phases = [ "installPhase" ];
  installPhase = ''
    mkdir -p $out/zcash-params/
    cp ${sapling-spend-params} $out/zcash-params/sapling-spend.params
    cp ${sapling-output-params} $out/zcash-params/sapling-output.params
  '';
}
