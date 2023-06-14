#! /usr/bin/env python3
# SPDX-FileCopyrightText: 2023 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

import os
import re
import sys
import json
import subprocess
import argparse
from dataclasses import dataclass
from typing import List, Optional

sys.path.append("docker/build")
from util.upload import *


def upload_ubuntu(args: Arguments):

    with open("dput.cfg", "w") as dput_cfg:
        dput_cfg.write(
            f"""
[DEFAULT]
login	 = *
method = ftp
hash = md5
allow_unsigned_uploads = 0
allow_dcut = 0
run_lintian = 0
run_dinstall = 0
check_version = 0
scp_compress = 0
post_upload_command	=
pre_upload_command =
passive_ftp = 1
default_host_main	=
allowed_distributions	= (?!UNRELEASED)

[tezos-serokell]
fqdn      = ppa.launchpad.net
method    = ftp
incoming  = ~serokell/ubuntu/tezos
login     = anonymous

[tezos-rc-serokell]
fqdn        = ppa.launchpad.net
method      = ftp
incoming    = ~serokell/ubuntu/tezos-rc
login       = anonymous

[tezos-test-serokell]
fqdn        = ppa.launchpad.net
method      = ftp
incoming    = ~serokell/ubuntu/tezos-test
login       = anonymous
    """
        )

    octez_version = os.getenv("OCTEZ_VERSION", None)

    if args.test:
        launchpad_ppa = "tezos-test-serokell"
    elif re.search("v.*-rc[0-9]*", octez_version):
        launchpad_ppa = "tezos-rc-serokell"
    else:
        launchpad_ppa = "tezos-serokell"

    source_packages_path = args.directory

    packages = get_artifact_list(args)

    for f in filter(lambda x: x.endswith(".changes"), packages):
        subprocess.check_call(
            f"execute-dput -c dput.cfg {launchpad_ppa} {f}",
            shell=True,
        )


def main(args: Optional[Arguments] = None):

    parser.set_defaults(os="ubuntu")

    if args is None:
        args = fill_args(parser.parse_args())

    upload_ubuntu(args)


if __name__ == "__main__":
    main()
