# SPDX-FileCopyrightText: 2019 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: MPL-2.0
{ pkgs ? import <nixpkgs> { }, timestamp ? "19700101" }:
let
  ignored_closures = [ "deb-packages" "rpm-packages" ];
  closures = builtins.attrValues
    (pkgs.lib.filterAttrs (n: v: !(builtins.elem n ignored_closures))
      (import ./. { inherit pkgs timestamp; }));
in pkgs.runCommandNoCC "release" { inherit closures; } ''
  mkdir -p $out
  for closure in $closures; do
  cp $closure/* $out/
  done
''
