# SPDX-FileCopyrightText: 2021 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ

let
  pkgs = import ../build/pkgs.nix { };
  common-src = builtins.fetchTarball {
    url = "https://pagure.io/copr/copr/archive/copr-cli-1.94-1/copr-copr-cli-1.94-1.tar.gz";
    sha256 = "0p6mrir6xhp9mi52dicd4j183bjvxlqdh03w57s7l22fcmrhsz26";
  };
  python-copr = pkgs.python39Packages.buildPythonApplication {
    propagatedBuildInputs = with pkgs.python39Packages;
      [ requests-toolbelt requests marshmallow six munch ];
    src = "${common-src}/python";
    name = "copr";
    version = "1.109";
  };
in pkgs.python39Packages.buildPythonApplication rec {
  propagatedBuildInputs = with pkgs.python39Packages;
    [ requests humanize jinja2 simplejson python-copr ];
  src = "${common-src}/cli";
  name = "copr-cli";
  version = "1.94.1";
  doCheck = false;
}
