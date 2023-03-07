#! /usr/bin/env python3
# SPDX-FileCopyrightText: 2023 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

import os
import re
import sys
import subprocess

sys.path.append("docker")
from supported_versions import fedora_versions

args = iter(sys.argv[1:])
source_packages_path = next(args)

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
"""
    )

octez_version = os.getenv("OCTEZ_VERSION", None)

if re.search("v.*-rc[0-9]*", octez_version):
    launchpad_ppa = "tezos-rc-serokell"
    copr_project = "@Serokell/Tezos-rc"
else:
    launchpad_ppa = "tezos-serokell"
    copr_project = "@Serokell/Tezos"

for f in filter(lambda x: x.endswith(".changes"), os.listdir(source_packages_path)):
    subprocess.call(
        f"execute-dput -c dput.cfg {launchpad_ppa} {os.path.join(source_packages_path, f)}",
        shell=True,
    )

archs = ["x86_64", "aarch64"]
chroot = next(args, None)
if chroot is None:
    chroots = [
        f"fedora-{version}-{arch}" for version in fedora_versions for arch in archs
    ]
else:
    chroots = [chroot]

chroots = " ".join(f"-r {chroot}" for chroot in chroots)

for f in filter(lambda x: x.endswith(".src.rpm"), os.listdir(source_packages_path)):
    subprocess.call(
        f"/run/wrappers/bin/sudo -u copr-uploader /run/current-system/sw/bin/copr-cli build {chroots} --nowait {copr_project} {os.path.join(source_packages_path, f)}",
        shell=True,
    )
