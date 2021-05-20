# SPDX-FileCopyrightText: 2021 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ

let pkgs = (import ../. {}).pkgs;
in ( pkgs.python3.buildEnv.override  {
    extraLibs = with pkgs.python3Packages; [ pyyaml ];
}).env
