# SPDX-FileCopyrightText: 2021 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ
import os, shutil, subprocess

from typing import List

from .model import AbstractPackage
from .systemd import Service, print_service_file


def build_ubuntu_package(
    pkg: AbstractPackage,
    ubuntu_versions: List[str],
    build_deps: List[str],
    is_source: bool,
    source_archive_path: str = None,
):
    # ubuntu prohibits uppercase in packages names
    pkg_name = pkg.name.lower()
    dir = f"{pkg_name}-{pkg.meta.version}"
    cwd = os.path.dirname(__file__)
    date = subprocess.check_output(["date", "-R"]).decode().strip()

    if source_archive_path is None:
        pkg.fetch_sources(dir)
        pkg.gen_makefile(f"{dir}/Makefile")
        subprocess.run(["tar", "-czf", f"{dir}.tar.gz", dir], check=True)
    else:
        shutil.copy(f"{cwd}/../{source_archive_path}", f"{dir}.tar.gz")
        subprocess.run(["tar", "-xzf", f"{dir}.tar.gz"], check=True)
    for ubuntu_version in ubuntu_versions:
        os.chdir(dir)
        subprocess.run(["rm", "-r", "debian"])
        subprocess.run(["dh_make", "-syf" f"../{dir}.tar.gz"], check=True)
        for systemd_unit in pkg.systemd_units:
            if systemd_unit.service_file.service.environment_file is not None:
                systemd_unit.service_file.service.environment_file = (
                    systemd_unit.service_file.service.environment_file.lower()
                )
            if systemd_unit.suffix is None:
                unit_name = pkg_name
            else:
                unit_name = f"{pkg_name}-{systemd_unit.suffix}"
            out_path = (
                f"debian/{unit_name}@.service"
                if len(systemd_unit.instances) > 0
                else f"debian/{unit_name}.service"
            )
            print_service_file(systemd_unit.service_file, out_path)
            if systemd_unit.config_file is not None:
                shutil.copy(
                    f"{cwd}/defaults/{systemd_unit.config_file}",
                    f"debian/{unit_name}.default",
                )
            if systemd_unit.startup_script is not None:
                dest_path = f"debian/{systemd_unit.startup_script}"
                source_script_name = (
                    systemd_unit.startup_script
                    if systemd_unit.startup_script_source is None
                    else systemd_unit.startup_script_source
                )
                source_path = f"{cwd}/scripts/{source_script_name}"
                shutil.copy(source_path, dest_path)
            if systemd_unit.prestart_script is not None:
                dest_path = f"debian/{systemd_unit.prestart_script}"
                source_path = (
                    f"{cwd}/scripts/{systemd_unit.prestart_script}"
                    if systemd_unit.prestart_script_source is None
                    else f"{cwd}/scripts/{systemd_unit.prestart_script_source}"
                )
                shutil.copy(source_path, dest_path)
        pkg.gen_install("debian/install")
        pkg.gen_rules("debian/rules")
        pkg.gen_postinst("debian/postinst")
        pkg.gen_postrm("debian/postrm")
        pkg.gen_control_file(build_deps, "debian/control")
        pkg.gen_license("debian/copyright")
        subprocess.run(
            "rm debian/*.ex debian/*.EX debian/README*", shell=True, check=True
        )
        pkg.gen_changelog(ubuntu_version, pkg.meta.maintainer, date, "debian/changelog")
        subprocess.run(
            ["dpkg-buildpackage", "-S" if is_source else "-b", "-us", "-uc"],
            check=True,
        )
        os.chdir("..")

    subprocess.run(f"rm -rf {dir}", shell=True, check=True)
