# SPDX-FileCopyrightText: 2021 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA
import os, shutil, subprocess

from typing import List

from .model import AbstractPackage
from .systemd import print_service_file


def build_ubuntu_package(
    pkg: AbstractPackage,
    ubuntu_versions: List[str],
    build_deps: List[str],
    is_source: bool,
    source_archive_path: str = None,
    binaries_dir: str = None,
):
    for ubuntu_version in ubuntu_versions:
        # ubuntu prohibits uppercase in packages names
        pkg_name = pkg.name.lower()
        old_version = pkg.meta.version
        # debian build utils don't like '_' symbol in version
        fixed_version = pkg.meta.version.replace("_", "-")
        dir = f"{pkg_name}-{fixed_version}"
        cwd = os.path.dirname(__file__)
        date = subprocess.check_output(["date", "-R"]).decode().strip()
        if source_archive_path is None:
            pkg.fetch_sources(dir, binaries_dir)
            pkg.gen_buildfile(
                "/".join([dir, pkg.buildfile]), ubuntu_version, binaries_dir
            )
            subprocess.run(["tar", "-czf", f"{dir}.tar.gz", dir], check=True)
        else:
            shutil.copy(f"{cwd}/../{source_archive_path}", f"{dir}.tar.gz")
            subprocess.run(["tar", "-xzf", f"{dir}.tar.gz"], check=True)
        pkg.meta.version = fixed_version

        os.chdir(dir)
        subprocess.run(["rm", "-r", "debian"])
        subprocess.run(["dh_make", "-syf" f"../{dir}.tar.gz"], check=True)
        for systemd_unit in pkg.systemd_units:
            if systemd_unit.service_file.service.environment_files is not None:
                systemd_unit.service_file.service.environment_files = [
                    x.lower()
                    for x in systemd_unit.service_file.service.environment_files
                ]
            if systemd_unit.suffix is None:
                unit_name = pkg_name
            else:
                unit_name = f"{pkg_name}-{systemd_unit.suffix}"
            out_path = (
                f"debian/{unit_name}@.service"
                if systemd_unit.instances is not None
                else f"debian/{unit_name}.service"
            )
            print_service_file(systemd_unit.service_file, out_path)
            if systemd_unit.config_file is not None:
                default_name = (
                    unit_name if systemd_unit.instances is None else f"{unit_name}@"
                )
                default_path = f"debian/{default_name}.default"
                shutil.copy(f"{cwd}/defaults/{systemd_unit.config_file}", default_path)
                if systemd_unit.config_file_append is not None:
                    with open(default_path, "a") as def_file:
                        def_file.write("\n".join(systemd_unit.config_file_append))

            for script, script_source in [
                (systemd_unit.startup_script, systemd_unit.startup_script_source),
                (systemd_unit.prestart_script, systemd_unit.prestart_script_source),
                (systemd_unit.poststop_script, systemd_unit.poststop_script_source),
            ]:
                if script is not None:
                    dest_path = f"debian/{script}"
                    source_script_name = (
                        script if script_source is None else script_source
                    )
                    source_path = f"{cwd}/scripts/{source_script_name}"
                    shutil.copy(source_path, dest_path)

            for script in pkg.additional_scripts:
                dest_path = f"debian/{script.name}"
                source_path = f"{cwd}/scripts/{script.local_file_name}"
                with open(source_path, "r") as src:
                    with open(dest_path, "w") as dst:
                        dst.write(script.transform(src.read()))

        # Patches only make sense when we're reusing the old sources that are not static binary
        if (
            len(pkg.patches) > 0
            and source_archive_path is not None
            and binaries_dir is None
        ):
            os.makedirs("debian/patches")
            with open("debian/patches/series", "w") as f:
                for patch in pkg.patches:
                    shutil.copy(f"{cwd}/patches/{patch}", f"debian/patches/{patch}")
                    f.write(patch)
        with open("debian/compat", "w") as f:
            f.write("10")
        pkg.gen_install("debian/install")
        pkg.gen_links("debian/links")
        pkg.gen_rules("debian/rules", ubuntu_version, binaries_dir)
        pkg.gen_postinst("debian/postinst")
        pkg.gen_postrm("debian/postrm")
        pkg.gen_control_file(build_deps, ubuntu_version, "debian/control")
        # License is downloaded from the tezos repo, thus version should be without workarounds
        pkg.meta.version = old_version
        pkg.gen_license("debian/copyright")
        pkg.meta.version = fixed_version
        subprocess.run(
            "rm -f debian/*.ex debian/*.EX debian/README*", shell=True, check=True
        )
        pkg.gen_changelog(ubuntu_version, pkg.meta.maintainer, date, "debian/changelog")
        subprocess.run(
            ["dpkg-buildpackage", "-S" if is_source else "-b", "-us", "-uc"],
            check=True,
        )
        os.chdir("..")
        pkg.meta.version = old_version

        subprocess.run(f"rm -rf {dir}", shell=True, check=True)
