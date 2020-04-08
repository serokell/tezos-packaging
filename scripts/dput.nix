# SPDX-FileCopyrightText: 2019 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: MPL-2.0

{ writeShellScriptBin, fetchbzr, python2 }:
let
  src = fetchbzr {
    url = "lp:~alexlist/dput/trunk";
    rev = "1s";
    sha256 = "17p2gbq0qplm818fzdr1z45hn39k26wz2rbn2rbm9csfbw9833zy";
  };
in writeShellScriptBin "dput" ''${python2}/bin/python ${src}/dput "$@"''
