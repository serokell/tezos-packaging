#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2022 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

import os
import sys
import shlex
import shutil
import subprocess
from typing import Optional
from package.package_generator import make_ubuntu_parser
from package.util.build import parser, build_fedora, build_ubuntu
from package.util.build import main as build
from package.util.sign import sign_fedora, sign_ubuntu
import package.util.sign as sign
import package.util.upload as upload
from package.util.upload import upload_ubuntu, upload_fedora

parser.add_argument(
    "--gpg-sign",
    "-s",
    help="provide an identity to sign packages",
    type=str,
)
# --upload will perform upload to regular repositories
# --upload epel will upload for epel-x86_64 chroot on copr
parser.add_argument(
    "--upload",
    help="upload packages to the specified repository",
    default=None,
    const="regular",
    nargs="?",
)


args = parser.parse_args()

artifacts = build(args)

if args.gpg_sign:
    sign.main(sign.Arguments(args.os, args.output_dir, artifacts, args.gpg_sign))

    if args.upload:
        upload.main(
            upload.Arguments(args.os, args.output_dir, artifacts, args.upload, False)
        )

elif args.upload:
    raise Exception("You have to sign packages before uploading them.")
