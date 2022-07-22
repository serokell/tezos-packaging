# SPDX-FileCopyrightText: 2021 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

import os, shutil, argparse

from .fedora import build_fedora_package
from .packages import packages, sapling_package
from .ubuntu import build_ubuntu_package


def get_ubuntu_run_deps(args):
    """
    List all the ubuntu run dependencies. Return an empty list when using prebuilt static binaries.
    """
    if args.binaries_dir:
        return []

    return [
        "libev-dev",
        "libgmp-dev",
        "libhidapi-dev",
        "libffi-dev",
        "zlib1g-dev",
        "libpq-dev",
    ]


def get_fedora_run_deps(args):
    """
    List all the fedora run dependencies. Return an empty list when using prebuilt static binaries.
    """
    if args.binaries_dir:
        return []

    return [
        "libev-devel",
        "gmp-devel",
        "hidapi-devel",
        "libffi-devel",
        "zlib-devel",
        "libpq-devel",
    ]


def get_build_deps(args):
    """
    List all the common build dependencies. Return an empty list when using prebuilt static binaries.
    """
    if args.binaries_dir:
        return ["make", "wget"]

    return [
        "make",
        "m4",
        "perl",
        "pkg-config",
        "wget",
        "unzip",
        "rsync",
        "gcc",
        "cargo",
        "opam",
        "git",
        "autoconf",
        "coreutils",
    ]


is_ubuntu = None
is_source = None
package_to_build = None
source_archive = None

parser = argparse.ArgumentParser()
parser.add_argument("--os", required=True)
parser.add_argument("--type", help="package type", required=True)
parser.add_argument("--package", help="specify binary to package")
parser.add_argument(
    "--output-dir",
    help="provide a directory to place the built packages",
    default="out",
)
parser.add_argument(
    "--binaries-dir",
    help="provide a directory with exiting prebuilt binaries",
    type=os.path.abspath,
)
parser.add_argument(
    "--build-sapling-package",
    help="whether to build the sapling-params package",
    action="store_true",
)
parser.add_argument(
    "--sources", help="specify source archive for single ubuntu package"
)
parser.set_defaults(build_sapling_package=False)
args = parser.parse_args()

if args.os == "ubuntu":
    is_ubuntu = True
elif args.os == "fedora":
    is_ubuntu = False
else:
    raise Exception(
        "Unexpected package target OS, only 'ubuntu' and 'fedora' are supported."
    )

if args.type == "source":
    is_source = True
elif args.type == "binary":
    is_source = False
else:
    raise Exception(
        "Unexpected package format, only 'source' and 'binary' are supported."
    )

package_to_build = args.package
source_archive = args.sources

if is_ubuntu:
    run_deps = get_ubuntu_run_deps(args)
else:
    run_deps = get_fedora_run_deps(args)

build_deps = get_build_deps(args)

common_deps = run_deps + build_deps

ubuntu_versions = [
    "bionic",  # 18.04
    "focal",  # 20.04
    "jammy",  # 22.04
]

pwd = os.getcwd()
home = os.environ["HOME"]

packages_to_build = packages

if args.build_sapling_package:
    packages.append(sapling_package)

for package in packages_to_build:
    if package_to_build is None or package.name == package_to_build:
        if is_ubuntu:
            build_ubuntu_package(
                package,
                ubuntu_versions,
                common_deps,
                is_source,
                source_archive,
                args.binaries_dir,
            )
        else:
            build_fedora_package(
                package, build_deps, run_deps, is_source, args.binaries_dir
            )

os.makedirs(args.output_dir, exist_ok=True)
if not is_source:
    if is_ubuntu:
        exts = [".deb"]
    else:
        exts = [".rpm"]
else:
    if is_ubuntu:
        exts = [".orig.tar.gz", ".dsc", ".changes", ".debian.tar.xz", ".buildinfo"]
    else:
        exts = [".src.rpm"]
if is_ubuntu:
    artifacts_dir = "."
else:
    subdir = "SRPMS" if is_source else "RPMS/x86_64"
    artifacts_dir = f"{home}/rpmbuild/{subdir}"
for f in os.listdir(artifacts_dir):
    for ext in exts:
        if f.endswith(ext):
            shutil.copy(f"{artifacts_dir}/{f}", os.path.join(args.output_dir, f))
