# SPDX-FileCopyrightText: 2019 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: MPL-2.0
{ stdenv, musl, netbsd }:
let
  getconf = builtins.fetchurl https://raw.githubusercontent.com/alpinelinux/aports/master/main/musl/getconf.c;
  getent = builtins.fetchurl https://raw.githubusercontent.com/alpinelinux/aports/master/main/musl/getent.c;
  isMusl = stdenv.hostPlatform.isMusl;
in
stdenv.mkDerivation {
  pname = "musl-bin";
  version = musl.version;
  srcs = [
    getconf
    getent
  ];
  buildInputs = [ musl ];
  unpackPhase = ''
    cp $srcs .
  '';
  buildPhase = ''
    ${if !isMusl then "musl-gcc" else "$CC"} *-getconf.c -o getconf
    ${if !isMusl then "musl-gcc" else "$CC"} *-getent.c -o getent
  '';
  installPhase = ''
    mkdir -p $out/bin
    install -D ./getconf ./getent $out/bin
  '';
}
