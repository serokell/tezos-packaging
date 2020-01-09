# SPDX-FileCopyrightText: 2019 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: MPL-2.0
{ pkgs ? import <nixpkgs> { }, timestamp ? "19700101" }:
let closures = builtins.attrValues (import ./. { inherit pkgs timestamp; });
in pkgs.runCommandNoCC "release" { inherit closures; } ''
  mkdir -p $out
  for closure in $closures; do
  cp $closure/* $out/
  done
''
