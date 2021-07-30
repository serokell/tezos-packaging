# SPDX-FileCopyrightText: 2020 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ

import os, shutil, argparse

from .fedora import build_fedora_package
from .packages import packages
from .ubuntu import build_ubuntu_package

is_ubuntu = None
is_source = None
package_to_build = None
source_archive = None

parser = argparse.ArgumentParser()
parser.add_argument("--os", required=True)
parser.add_argument("--type", help="package type", required=True)
parser.add_argument("--package", help="specify binary to package")
parser.add_argument(
    "--sources", help="specify source archive for single ubuntu package"
)
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
    run_deps = ["libev-dev", "libgmp-dev", "libhidapi-dev", "libffi-dev"]
else:
    run_deps = ["libev-devel", "gmp-devel", "hidapi-devel", "libffi-devel"]
build_deps = [
    "make",
    "m4",
    "perl",
    "pkg-config",
    "wget",
    "unzip",
    "rsync",
    "gcc",
    "cargo",
]
common_deps = run_deps + build_deps

ubuntu_versions = [
    "bionic",  # 18.04
    "focal",  # 20.04
    "hirsute",  # 21.04
]

pwd = os.getcwd()
home = os.environ["HOME"]

for package in packages:
    if package_to_build is None or package.name == package_to_build:
        if is_ubuntu:
            build_ubuntu_package(
                package, ubuntu_versions, common_deps, is_source, source_archive
            )
        else:
            build_fedora_package(package, build_deps, run_deps, is_source)

os.mkdir("out")
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
            shutil.copy(f"{artifacts_dir}/{f}", os.path.join("out", f))
