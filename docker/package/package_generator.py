# SPDX-FileCopyrightText: 2020 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ

import os, shutil, sys, subprocess, json, argparse
from distutils.dir_util import copy_tree

from .model import OpamBasedPackage
from .systemd import print_service_file
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

ubuntu_versions = ["bionic", "focal", "groovy"]  # 18.04  # 20.04  # 20.10

pwd = os.getcwd()
home = os.environ["HOME"]

for package in packages:
    if package_to_build is None or package.name == package_to_build:
        if is_ubuntu:
            build_ubuntu_package(
                package, ubuntu_versions, common_deps, is_source, source_archive
            )
        else:
            dir = f"{package.name}-{version}"
            if source_archive is not None:
                raise Exception(
                    "Sources archive provision isn't supported for Fedora packages"
                )
            for systemd_unit in package.systemd_units:
                if systemd_unit.suffix is None:
                    out_name = (
                        f"{dir}/{package.name}@.service"
                        if len(systemd_unit.instances) > 0
                        else f"{dir}/{package.name}.service"
                    )
                    print_service_file(systemd_unit.service_file, out_name)
                    if systemd_unit.config_file is not None:
                        shutil.copy(
                            f"{os.path.dirname(__file__)}/defaults/{systemd_unit.config_file}",
                            f"{dir}/{package.name}.default",
                        )
                else:
                    out_name = (
                        f"{dir}/{package.name}-{systemd_unit.suffix}@.service"
                        if len(systemd_unit.instances) > 0
                        else f"{dir}/{package.name}-{systemd_unit.suffix}.service"
                    )
                    print_service_file(systemd_unit.service_file, out_name)
                    if systemd_unit.config_file is not None:
                        shutil.copy(
                            f"{os.path.dirname(__file__)}/defaults/{systemd_unit.config_file}",
                            f"{dir}/{package.name}-{systemd_unit.suffix}.default",
                        )
                if systemd_unit.startup_script is not None:
                    dest = f"{dir}/{systemd_unit.startup_script}"
                    if systemd_unit.startup_script_source is not None:
                        source = f"{os.path.dirname(__file__)}/scripts/{systemd_unit.startup_script_source}"
                    else:
                        source = f"{os.path.dirname(__file__)}/scripts/{systemd_unit.startup_script}"
                    shutil.copy(source, dest)
                if systemd_unit.prestart_script is not None:
                    dest = f"{dir}/{systemd_unit.prestart_script}"
                    if systemd_unit.prestart_script_source is not None:
                        source = f"{os.path.dirname(__file__)}/scripts/{systemd_unit.prestart_script_source}"
                    else:
                        source = f"{os.path.dirname(__file__)}/scripts/{systemd_unit.prestart_script}"
                    shutil.copy(source, dest)
            subprocess.run(["tar", "-czf", f"{dir}.tar.gz", dir], check=True)
            os.makedirs(f"{home}/rpmbuild/SPECS", exist_ok=True)
            os.makedirs(f"{home}/rpmbuild/SOURCES", exist_ok=True)
            package.gen_spec_file(
                common_deps, run_deps, f"{home}/rpmbuild/SPECS/{package.name}.spec"
            )
            os.rename(f"{dir}.tar.gz", f"{home}/rpmbuild/SOURCES/{dir}.tar.gz")
            subprocess.run(
                [
                    "rpmbuild",
                    "-bs" if is_source else "-bb",
                    f"{home}/rpmbuild/SPECS/{package.name}.spec",
                ],
                check=True,
            )
            subprocess.run(f"rm -rf {dir}", shell=True, check=True)

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
