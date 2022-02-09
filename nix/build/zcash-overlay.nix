# SPDX-FileCopyrightText: 2020 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ

# zcash-params required for building some of the tezos binaries
# and for running tests
final: prev:
with final.nixpkgs;
let
  zcash = callPackage ./zcash.nix { };

  inject-zcash = oa: {
    nativeBuildInputs = oa.nativeBuildInputs ++ [ makeWrapper ];
    postFixup = ''
      for bin in $(find $out/bin -not -name '*.sh' -type f -executable); do
        wrapProgram "$bin" --prefix XDG_DATA_DIRS : ${zcash}
      done
    '';
  };

  relevant-packages =
    "tezos-(accuser|node|codec|admin-client|baker|endorser|signer).*";
in builtins.mapAttrs (name: pkg:
  if !isNull (builtins.match relevant-packages name) then
    pkg.overrideAttrs inject-zcash
  else
    pkg) prev
