# SPDX-FileCopyrightText: 2020 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ

import os, shutil, sys, subprocess, json, argparse
from distutils.dir_util import copy_tree

from .model import OpamBasedPackage, print_service_file
from .packages import packages

is_ubuntu = None
is_source = None
package_to_build = None
source_archive = None

parser = argparse.ArgumentParser()
parser.add_argument("--os", required=True)
parser.add_argument("--type", help="package type", required=True)
parser.add_argument("--package", help="specify binary to package")
parser.add_argument("--sources", help="specify source archive for single ubuntu package")
args = parser.parse_args()

if args.os == "ubuntu":
    is_ubuntu = True
elif args.os == "fedora":
    is_ubuntu = False
else:
    raise Exception("Unexpected package target OS, only 'ubuntu' and 'fedora' are supported.")

if args.type == "source":
    is_source = True
elif args.type == "binary":
    is_source = False
else:
    raise Exception("Unexpected package format, only 'source' and 'binary' are supported.")

package_to_build = args.package
source_archive = args.sources

date = subprocess.check_output(["date", "-R"]).decode().strip()
meta = json.load(open(f"{os.path.dirname(__file__)}/../../meta.json", "r"))

if is_ubuntu:
    run_deps = ["libev-dev", "libgmp-dev", "libhidapi-dev", "libffi-dev"]
else:
    run_deps = ["libev-devel", "gmp-devel", "hidapi-devel", "libffi-devel"]
build_deps = ["make", "m4", "perl", "pkg-config", "wget", "unzip", "rsync", "gcc", "cargo"]
common_deps = run_deps + build_deps

version = os.environ["TEZOS_VERSION"][1:]
release = f"{meta['release']}"

ubuntu_versions = [
    "bionic",  # 18.04
    "focal",  # 20.04
    "groovy"  # 20.10
]

pwd = os.getcwd()
home = os.environ["HOME"]

for package in packages:
    if package_to_build is None or package.name == package_to_build:
        if is_ubuntu:
            dir = f"{package.name.lower()}-{version}"
        else:
            dir = f"{package.name}-{version}"
        if source_archive is None:
            package.fetch_sources(dir)
            package.gen_makefile(f"{dir}/Makefile")
            if not is_ubuntu:
                subprocess.run(["wget", "-q", "-O", f"{dir}/LICENSE", f"https://gitlab.com/tezos/tezos/-/raw/v{version}/LICENSE"], check=True)
        if is_ubuntu:
            if source_archive is None:
                subprocess.run(["tar", "-czf", f"{dir}.tar.gz", dir], check=True)
            else:
                shutil.copy(f"{os.path.dirname(__file__)}/../{source_archive}", f"{dir}.tar.gz")
                subprocess.run(["tar", "-xzf", f"{dir}.tar.gz"], check=True)
            for ubuntu_version in ubuntu_versions:
                os.chdir(dir)
                subprocess.run(["rm", "-r", "debian"])
                subprocess.run(["dh_make", "-syf" f"../{dir}.tar.gz"], check=True)
                for systemd_unit in package.systemd_units:
                    if systemd_unit.service_file.service.environment_file is not None:
                        systemd_unit.service_file.service.environment_file = systemd_unit.service_file.service.environment_file.lower()
                    if systemd_unit.suffix is None:
                        if systemd_unit.config_file is not None:
                            shutil.copy(f"{os.path.dirname(__file__)}/defaults/{systemd_unit.config_file}",
                                        f"debian/{package.name.lower()}.default")
                        out_name = (f"debian/{package.name.lower()}@.service"
                                    if len(systemd_unit.instances) > 0
                                    else f"debian/{package.name.lower()}.service")
                        print_service_file(systemd_unit.service_file, out_name)
                    else:
                        out_name = (f"debian/{package.name.lower()}-{systemd_unit.suffix}@.service"
                                    if len(systemd_unit.instances) > 0
                                    else f"debian/{package.name.lower()}-{systemd_unit.suffix}.service")
                        print_service_file(systemd_unit.service_file, out_name)
                        if systemd_unit.config_file is not None:
                            shutil.copy(f"{os.path.dirname(__file__)}/defaults/{systemd_unit.config_file}",
                                        f"debian/{package.name.lower()}-{systemd_unit.suffix}.default")
                    if systemd_unit.startup_script is not None:
                        shutil.copy(f"{os.path.dirname(__file__)}/scripts/{systemd_unit.startup_script}", f"debian/{systemd_unit.startup_script}")
                package.gen_install("debian/install")
                package.gen_postinst("debian/postinst")
                package.gen_postrm("debian/postrm")
                package.gen_control_file(common_deps, "debian/control")
                subprocess.run(["wget", "-q", "-O", "debian/copyright", f"https://gitlab.com/tezos/tezos/-/raw/v{version}/LICENSE"], check=True)
                subprocess.run("rm debian/*.ex debian/*.EX debian/README*", shell=True, check=True)
                package.gen_changelog(ubuntu_version, meta["maintainer"], date, "debian/changelog")
                package.gen_rules("debian/rules")
                subprocess.run(["dpkg-buildpackage", "-S" if is_source else "-b", "-us", "-uc"],
                            check=True)
                os.chdir("..")
        else:
            if source_archive is not None:
                raise Exception("Sources archive provision isn't supported for Fedora packages")
            for systemd_unit in package.systemd_units:
                if systemd_unit.suffix is None:
                    out_name = (f"{dir}/{package.name}@.service"
                                    if len(systemd_unit.instances) > 0
                                    else f"{dir}/{package.name}.service")
                    print_service_file(systemd_unit.service_file, out_name)
                    if systemd_unit.config_file is not None:
                        shutil.copy(f"{os.path.dirname(__file__)}/defaults/{systemd_unit.config_file}",
                                    f"{dir}/{package.name}.default")
                else:
                    out_name = (f"{dir}/{package.name}-{systemd_unit.suffix}@.service"
                                    if len(systemd_unit.instances) > 0
                                    else f"{dir}/{package.name}-{systemd_unit.suffix}.service")
                    print_service_file(systemd_unit.service_file, out_name)
                    if systemd_unit.config_file is not None:
                        shutil.copy(f"{os.path.dirname(__file__)}/defaults/{systemd_unit.config_file}",
                                    f"{dir}/{package.name}-{systemd_unit.suffix}.default")
                if systemd_unit.startup_script is not None:
                    shutil.copy(f"{os.path.dirname(__file__)}/scripts/{systemd_unit.startup_script}", f"{dir}/{systemd_unit.startup_script}")
            subprocess.run(["tar", "-czf", f"{dir}.tar.gz", dir], check=True)
            os.makedirs(f"{home}/rpmbuild/SPECS", exist_ok=True)
            os.makedirs(f"{home}/rpmbuild/SOURCES", exist_ok=True)
            package.gen_spec_file(common_deps, run_deps, f"{home}/rpmbuild/SPECS/{package.name}.spec")
            os.rename(f"{dir}.tar.gz", f"{home}/rpmbuild/SOURCES/{dir}.tar.gz")
            subprocess.run(["rpmbuild", "-bs" if is_source else "-bb", f"{home}/rpmbuild/SPECS/{package.name}.spec"],
                           check = True)
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
