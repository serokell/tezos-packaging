#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2023 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

import os
import sys
import shlex
import shutil
import subprocess
from typing import Optional, List

from package.package_generator import make_ubuntu_parser

from build.util.build import parser
from build.ubuntu.build import build_ubuntu
from build.fedora.build import build_fedora

from build.ubuntu.sign import sign_ubuntu
from build.fedora.sign import sign_fedora

import build.util.sign as sign
from build.ubuntu.sign import sign_ubuntu
from build.fedora.sign import sign_fedora

import build.util.upload as upload
from build.ubuntu.upload import upload_ubuntu
from build.fedora.upload import upload_fedora


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


def build_wrapper(args) -> List[str]:

    if args.os == "ubuntu":
        artifacts = build_ubuntu(args)
    elif args.os == "fedora":
        artifacts = build_fedora(args)

    return artifacts


def sign_wrapper(args: sign.Arguments):

    if args.os == "ubuntu":
        sign_ubuntu(args)
    elif args.os == "fedora":
        sign_fedora(args)


def upload_wrapper(args: upload.Arguments):

    if args.os == "ubuntu":
        upload_ubuntu(args)
    elif args.os == "fedora":
        upload_fedora(args)


args, _ = parser.parse_known_args()

if args.os == "ubuntu":
    args = make_ubuntu_parser(parser).parse_args()
elif args.os == "fedora":
    args = parser.parse_args()

artifacts = build_wrapper(args)

if args.gpg_sign:
    sign_wrapper(sign.Arguments(args.os, args.output_dir, artifacts, args.gpg_sign))

    if args.upload:
        upload_wrapper(
            upload.Arguments(args.os, args.output_dir, artifacts, args.upload, False)
        )

elif args.upload:
    raise Exception("You have to sign packages before uploading them.")
