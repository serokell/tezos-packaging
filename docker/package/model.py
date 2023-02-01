# SPDX-FileCopyrightText: 2021 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

import os, subprocess
import re
import shutil
import stat
from copy import deepcopy
from abc import abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Callable, Optional

from .meta import PackagesMeta
from .systemd import (
    Install,
    Service,
    ServiceFile,
    SystemdUnit,
    Unit,
)


@dataclass
class AdditionalScript:
    local_file_name: str
    name: str
    symlink_name: Optional[str] = field(default_factory=None)
    # expected to be pure
    transform: Callable[[str], str] = field(default_factory=lambda x: x)


class AbstractPackage:

    buildfile = "Makefile"

    additional_scripts: List[AdditionalScript] = []

    @abstractmethod
    def fetch_sources(self, out_dir, binaries_dir=None):
        pass

    @abstractmethod
    def gen_control_file(self, out):
        pass

    @abstractmethod
    def get_spec_file(self, out):
        pass

    @abstractmethod
    def gen_buildfile(self, out, ubuntu_version, binaries_dir=None):
        pass

    def gen_changelog(self, ubuntu_version, maintainer, date, out):
        changelog_contents = f"""{self.name.lower()} ({self.meta.ubuntu_epoch}:{self.meta.version}-0ubuntu{self.meta.release}~{ubuntu_version}) {ubuntu_version}; urgency=medium

  * Publish {self.meta.version}-{self.meta.release} version of {self.name}

 -- {maintainer} {date}"""
        with open(out, "w") as f:
            f.write(changelog_contents)

    @abstractmethod
    def gen_rules(self, out, ubuntu_version, binaries_dir=None):
        pass

    def gen_install(self, out):
        scripts = set()
        for unit in self.systemd_units:
            for script in [
                unit.startup_script,
                unit.prestart_script,
                unit.poststop_script,
            ]:
                if script is not None:
                    scripts.add(script)
        scripts |= set(map(lambda x: x.name, self.additional_scripts))
        if len(scripts) > 0:
            install_contents = "\n".join([f"debian/{x} usr/bin" for x in scripts])
            with open(out, "w") as f:
                f.write(install_contents)

    def gen_links(self, out):
        with open(out, "w") as f:
            f.write(
                "\n".join(
                    [
                        f"/usr/bin/{x.name} /usr/bin/{x.symlink_name}"
                        for x in self.additional_scripts
                        if x.symlink_name is not None
                    ]
                )
            )

    @abstractmethod
    def gen_postinst(self, out):
        pass

    @abstractmethod
    def gen_postrm(self, out):
        pass

    @abstractmethod
    def gen_license(self, out):
        pass


def gen_spec_systemd_part(package):
    systemd_units = package.systemd_units
    scripts = set()
    for unit in systemd_units:
        for script in [unit.startup_script, unit.prestart_script, unit.poststop_script]:
            if script is not None:
                scripts.add(script)
    config_files = [x.config_file for x in systemd_units if x.config_file is not None]
    install_unit_files = ""
    systemd_unit_files = ""
    systemd_units_post = ""
    systemd_units_preun = ""
    systemd_units_postun = ""
    if len(config_files) > 0:
        install_default = f"mkdir -p %{{buildroot}}/%{{_sysconfdir}}/default\n"
    else:
        install_default = ""
    # Note: this covers all environment files too because there are either:
    # 1. the default files of a systemd unit in this package
    # 2. the default files of a systemd unit in another package
    # 3. files that we don't create during installation (e.g. for instantiated services)
    default_files = ""
    environment_files = ""
    for systemd_unit in package.systemd_units:
        if systemd_unit.suffix is None:
            service_name = f"{package.name.lower()}"
        else:
            service_name = f"{package.name.lower()}-{systemd_unit.suffix}"
        if systemd_unit.instances is not None:
            service_name = f"{service_name}@"
        install_unit_files += (
            f"install -m 644 {service_name}.service %{{buildroot}}/%{{_unitdir}}\n"
        )
        systemd_unit_files += f"%{{_unitdir}}/{service_name}.service\n"
        systemd_units_post += f"%systemd_post {service_name}.service\n"
        systemd_units_preun += f"%systemd_preun {service_name}.service\n"
        systemd_units_postun += f"%systemd_postun_with_restart {service_name}.service\n"
        if systemd_unit.config_file is not None:
            install_default += (
                f"install -m 644 {service_name}.default "
                + f"%{{buildroot}}/%{{_sysconfdir}}/default/{service_name}\n"
            )
            default_files += f"%{{_sysconfdir}}/default/{service_name}\n"
    install_startup_scripts = ""
    systemd_startup_files = ""
    for script in scripts:
        if script is not None:
            install_startup_scripts += (
                f"install -m 0755 {script} %{{buildroot}}/%{{_bindir}}\n"
            )
            systemd_startup_files += f"%{{_bindir}}/{script}\n"
    systemd_deps = "systemd systemd-rpm-macros"
    systemd_install = f"""
mkdir -p %{{buildroot}}/%{{_unitdir}}
{install_unit_files}
{install_default}
{install_startup_scripts}
"""
    systemd_files = f"""
{systemd_startup_files}
{systemd_unit_files}
{default_files}
"""
    systemd_macros = f"""
%post
{systemd_units_post}
{package.postinst_steps}

%preun
{systemd_units_preun}

%postun
{systemd_units_postun}
{package.postrm_steps}
"""
    return systemd_deps, systemd_install, systemd_files, systemd_macros


def mk_dh_flags(package):
    return " ".join(
        [
            "--with systemd" if len(package.systemd_units) > 0 else "",
            "--with python3 --buildsystem=pybuild"
            if package.buildfile == "setup.py"
            else "",
        ]
    )


def gen_systemd_rules_contents(package, ubuntu_version, binaries_dir=None):
    package_name = package.name.lower()
    units = set()
    for systemd_unit in package.systemd_units:
        if systemd_unit.instances is None:
            if systemd_unit.suffix is not None:
                unit_name = f"{package_name}-{systemd_unit.suffix}"
            else:
                unit_name = f"{package_name}"
        else:
            if systemd_unit.suffix is not None:
                unit_name = f"{package_name}-{systemd_unit.suffix}@"
            else:
                unit_name = f"{package_name}@"
        units.add(unit_name)
    override_dh_install_init = "override_dh_installinit:\n" + "\n".join(
        f"	dh_installinit --name={unit_name}" for unit_name in units
    )
    override_dh_auto_install = (
        "override_dh_auto_install:\n"
        + "	dh_auto_install\n"
        + "\n".join(
            f"	dh_installsystemd --no-enable --no-start --name={unit_name} {unit_name}.service"
            for unit_name in units
        )
    )
    splice_if = lambda cond: lambda string: string if cond else ""
    is_pybuild = package.buildfile == "setup.py"
    pybuild_splice = splice_if(is_pybuild)
    rules_contents = f"""#!/usr/bin/make -f
# Disable usage of instructions from the ADX extension to avoid incompatibility
# with old CPUs, see https://gitlab.com/dannywillems/ocaml-bls12-381/-/merge_requests/135/
export BLST_PORTABLE=yes
{splice_if(binaries_dir)("export DEB_BUILD_OPTIONS=nostrip")}
{pybuild_splice(f'''
export PYBUILD_NAME={package_name}
export PYBUILD_INTERPRETERS={"python3.8" if ubuntu_version != "jammy" else "python3"}
''')}
export DEB_CFLAGS_APPEND=-fPIC

%:
	dh $@ {mk_dh_flags(package)}

override_dh_systemd_enable:
	dh_systemd_enable {pybuild_splice("-O--buildsystem=pybuild")} --no-enable

override_dh_python3:
	dh_python3 --shebang=/usr/bin/${{PYBUILD_INTERPRETERS}}

override_dh_systemd_start:
	dh_systemd_start {pybuild_splice("-O--buildsystem=pybuild")} --no-start

{override_dh_auto_install if len(package.systemd_units) > 1 and not is_pybuild else ""}

{override_dh_install_init if len(package.systemd_units) > 1 else ""}
"""
    return rules_contents


class TezosBinaryPackage(AbstractPackage):
    def __init__(
        self,
        name: str,
        desc: str,
        meta: PackagesMeta,
        dune_filepath: str,
        systemd_units: List[SystemdUnit] = [],
        target_proto: str = None,
        postinst_steps: str = "",
        postrm_steps: str = "",
        additional_scripts: List[AdditionalScript] = [],
        additional_native_deps: List[str] = [],
        patches: List[str] = [],
    ):
        self.name = name
        self.desc = desc
        self.systemd_units = systemd_units
        self.target_proto = target_proto
        self.postinst_steps = postinst_steps
        self.postrm_steps = postrm_steps
        self.additional_native_deps = additional_native_deps
        self.additional_scripts = additional_scripts
        self.meta = meta
        self.dune_filepath = dune_filepath
        self.patches = patches

    def __get_os_specific_native_deps(self, os_name):
        return [
            x[os_name] if (isinstance(x, dict)) else x
            for x in self.additional_native_deps
            if isinstance(x, str) or (isinstance(x, dict) and os_name in x.keys())
        ]

    def fetch_sources(self, out_dir, binaries_dir=None):
        cwd = os.path.dirname(__file__)
        os.makedirs(out_dir)
        os.chdir(out_dir)

        # We'll be using the pre-built binaries as source.
        if binaries_dir:
            binary_name = self.name.replace("tezos", "octez")
            shutil.copy(f"{binaries_dir}/{binary_name}", binary_name)
        else:
            shutil.copytree(f"{cwd}/../sources/tezos", "tezos")
            shutil.copytree(f"{cwd}/../sources/opam-repository", "opam-repository")
            shutil.copy(f"{cwd}/scripts/build-binary.sh", "build-binary.sh")

        os.chdir("..")

    def gen_control_file(self, deps, ubuntu_version, out):
        str_build_deps = ", ".join(deps)
        str_additional_native_deps = ", ".join(
            self.__get_os_specific_native_deps("ubuntu")
        )
        file_contents = f"""
Source: {self.name.lower()}
Section: utils
Priority: optional
Maintainer: {self.meta.maintainer}
Build-Depends: debhelper (>=9), {"dh-systemd (>= 1.5), " if ubuntu_version != "jammy" else ""} autotools-dev, {str_build_deps}
Standards-Version: 3.9.6
Homepage: https://gitlab.com/tezos/tezos/

Package: {self.name.lower()}
Architecture: amd64 arm64
Depends: ${{shlibs:Depends}}, ${{misc:Depends}}, {str_additional_native_deps}
Description: {self.desc}
"""
        with open(out, "w") as f:
            f.write(file_contents)

    def gen_spec_file(self, build_deps, run_deps, out):
        binary_name = self.name.replace("tezos", "octez")
        build_requires = " ".join(build_deps)
        requires = " ".join(run_deps)
        str_additional_native_deps = ", ".join(
            self.__get_os_specific_native_deps("fedora")
        )
        (
            systemd_deps,
            systemd_install,
            systemd_files,
            systemd_macros,
        ) = gen_spec_systemd_part(self)
        version = self.meta.version.replace("-", "")

        scripts_install = "\n".join(
            [
                f"install -m 0755 {x.name} %{{buildroot}}/%{{_bindir}}/\n"
                for x in self.additional_scripts
            ]
        )

        symlinks_install = "\n".join(
            [
                f"ln -s %{{_bindir}}/{x.name} %{{buildroot}}/%{{_bindir}}/{x.symlink_name}"
                for x in self.additional_scripts
                if x.symlink_name is not None
            ]
        )

        additional_files_list = "\n".join(
            map(
                lambda x: "%{_bindir}/" + x,
                sum(
                    [
                        [x.name] + ([] if x.symlink_name is None else [x.symlink_name])
                        for x in self.additional_scripts
                    ],
                    [],
                ),
            )
        )

        file_contents = f"""
%define debug_package %{{nil}}
Name:    {self.name}
Version: {version}
Release: {self.meta.release}
Epoch: {self.meta.fedora_epoch}
Summary: {self.desc}
License: MIT
BuildArch: x86_64 aarch64
Source0: {self.name}-{version}.tar.gz
Source1: https://gitlab.com/tezos/tezos/tree/v{self.meta.version}/
BuildRequires: {build_requires} {systemd_deps}
Requires: {requires}, {str_additional_native_deps}
%description
{self.desc}
Maintainer: {self.meta.maintainer}
%prep
%setup -q
%build
%install
make {binary_name}
mkdir -p %{{buildroot}}/%{{_bindir}}
install -m 0755 {binary_name} %{{buildroot}}/%{{_bindir}}
ln -s %{{_bindir}}/{binary_name} %{{buildroot}}/%{{_bindir}}/{self.name}
{scripts_install}
{symlinks_install}
{systemd_install}
%files
%license LICENSE
{additional_files_list}
%{{_bindir}}/{binary_name}
%{{_bindir}}/{self.name}
{systemd_files}
{systemd_macros}
"""
        with open(out, "w") as f:
            f.write(file_contents)

    def gen_buildfile(self, out, ubuntu_version, binaries_dir=None):
        binary_name = self.name.replace("tezos", "octez")
        makefile_contents = f"""
.PHONY: install

BINDIR=/usr/bin

{binary_name}:
{f"	./build-binary.sh {self.dune_filepath} {binary_name}"
        if not binaries_dir
        else ""}


install: {binary_name}
	mkdir -p $(DESTDIR)$(BINDIR)
	cp $(CURDIR)/{binary_name} $(DESTDIR)$(BINDIR)
	ln -s $(BINDIR)/{binary_name} $(DESTDIR)$(BINDIR)/{self.name}
"""
        with open(out, "w") as f:
            f.write(makefile_contents)

    def gen_rules(self, out, ubuntu_version, binaries_dir=None):
        rules_contents = gen_systemd_rules_contents(self, ubuntu_version, binaries_dir)
        with open(out, "w") as f:
            f.write(rules_contents)

    def gen_postinst(self, out):
        postinst_contents = f"""#!/bin/sh

set -e

#DEBHELPER#

{self.postinst_steps}
"""
        postinst_contents = postinst_contents.replace(self.name, self.name.lower())
        with open(out, "w") as f:
            f.write(postinst_contents)

    def gen_postrm(self, out):
        postrm_contents = f"""#!/bin/sh

set -e

#DEBHELPER#

{self.postrm_steps}
"""
        postrm_contents = postrm_contents.replace(self.name, self.name.lower())
        with open(out, "w") as f:
            f.write(postrm_contents)

    def gen_license(self, out):
        subprocess.run(
            [
                "wget",
                "-q",
                "-O",
                out,
                f"https://gitlab.com/tezos/tezos/-/raw/{self.meta.license_version}/LICENSE",
            ],
            check=True,
        )


class TezosSaplingParamsPackage(AbstractPackage):
    def __init__(self, meta: PackagesMeta, params_revision: str):
        self.name = "tezos-sapling-params"
        self.desc = "Sapling params required in the runtime by the Tezos binaries"
        self.systemd_units = []
        self.targetProto = None
        self.meta = meta
        self.params_revision = params_revision
        self.patches = []

    def fetch_sources(self, out_dir, binaries_dir=None):
        os.makedirs(out_dir)
        subprocess.run(
            [
                "wget",
                "-P",
                out_dir,
                f"https://gitlab.com/tezos/opam-repository/-/raw/{self.params_revision}/zcash-params/sapling-spend.params",
            ]
        )
        subprocess.run(
            [
                "wget",
                "-P",
                out_dir,
                f"https://gitlab.com/tezos/opam-repository/-/raw/{self.params_revision}/zcash-params/sapling-output.params",
            ]
        )

    def gen_control_file(self, deps, ubuntu_version, out):
        file_contents = f"""
Source: {self.name}
Section: utils
Priority: optional
Maintainer: {self.meta.maintainer}
Build-Depends: debhelper (>=9), {"dh-systemd (>= 1.5), " if ubuntu_version != "jammy" else ""} autotools-dev, wget
Standards-Version: 3.9.6
Homepage: https://gitlab.com/tezos/tezos/

Package: {self.name.lower()}
Architecture: amd64 arm64
Depends: ${{shlibs:Depends}}, ${{misc:Depends}}
Description: {self.desc}
"""
        with open(out, "w") as f:
            f.write(file_contents)

    def gen_spec_file(self, build_deps, run_deps, out):
        version = self.meta.version.replace("-", "")
        file_contents = f"""
%define debug_package %{{nil}}
Name:    {self.name}
Version: {version}
Release: {self.meta.release}
Epoch: {self.meta.fedora_epoch}
Summary: {self.desc}
License: MIT
BuildArch: x86_64 aarch64
Source0: {self.name}-{version}.tar.gz
BuildRequires: wget
%description
{self.desc}
Maintainer: {self.meta.maintainer}
%prep
%setup -q
%build
%install
mkdir -p %{{buildroot}}/%{{_datadir}}/zcash-params
install -m 0755 sapling-spend.params %{{buildroot}}/%{{_datadir}}/zcash-params
install -m 0755 sapling-output.params %{{buildroot}}/%{{_datadir}}/zcash-params

%files
%license LICENSE
%{{_datadir}}/zcash-params/sapling-spend.params
%{{_datadir}}/zcash-params/sapling-output.params
"""
        with open(out, "w") as f:
            f.write(file_contents)

    def gen_buildfile(self, out, ubuntu_version, binaries_dir=None):
        file_contents = """
.PHONY: install

DATADIR=/usr/share/zcash-params/

tezos-sapling-params:

install: tezos-sapling-params
	mkdir -p $(DESTDIR)$(DATADIR)
	cp $(CURDIR)/sapling-spend.params $(DESTDIR)$(DATADIR)
	cp $(CURDIR)/sapling-output.params $(DESTDIR)$(DATADIR)
"""
        with open(out, "w") as f:
            f.write(file_contents)

    def gen_rules(self, out, ubuntu_version, binaries_dir=None):
        rules_contents = """#!/usr/bin/make -f

%:
	dh $@
"""
        with open(out, "w") as f:
            f.write(rules_contents)

    def gen_license(self, out):
        shutil.copy(f"{os.path.dirname(__file__)}/../../LICENSE", out)


class TezosBakingServicesPackage(AbstractPackage):

    # Sometimes we need to update the tezos-baking package in between
    # native releases, so we append an extra letter to the version of
    # the package.
    # This should be reset to "" whenever the native version is bumped.
    letter_version = "a"

    buildfile = "setup.py"

    def __gen_baking_systemd_unit(
        self, requires, description, environment_files, config_file, suffix
    ):
        return SystemdUnit(
            service_file=ServiceFile(
                Unit(
                    after=["network.target"],
                    requires=requires,
                    description=description,
                ),
                Service(
                    exec_start="/usr/bin/tezos-baking-start",
                    user="tezos",
                    state_directory="tezos",
                    environment_files=environment_files,
                    exec_start_pre=[
                        "+/usr/bin/setfacl -m u:tezos:rwx /run/systemd/ask-password",
                        "/usr/bin/tezos-baking-prestart",
                    ],
                    exec_stop_post=[
                        "+/usr/bin/setfacl -x u:tezos /run/systemd/ask-password"
                    ],
                    remain_after_exit=True,
                    type_="oneshot",
                    keyring_mode="shared",
                ),
                Install(wanted_by=["multi-user.target"]),
            ),
            suffix=suffix,
            config_file=config_file,
            startup_script="tezos-baking-start",
            prestart_script="tezos-baking-prestart",
        )

    def __init__(
        self,
        target_networks: List[str],
        network_protos: Dict[str, List[str]],
        meta: PackagesMeta,
        additional_native_deps: List[str],
    ):
        self.name = "tezos-baking"
        self.desc = "Package that provides systemd services that orchestrate other services from Tezos packages"
        self.meta = deepcopy(meta)
        self.additional_native_deps = additional_native_deps
        self.meta.version = self.meta.version + self.letter_version
        self.target_protos = set()
        self.patches = []
        for network in target_networks:
            for proto in network_protos[network]:
                self.target_protos.add(proto)
        self.systemd_units = []
        for network in target_networks:
            requires = [f"tezos-node-{network}.service"]
            for proto in network_protos[network]:
                requires.append(f"tezos-baker-{proto.lower()}@{network}.service")
            self.systemd_units.append(
                self.__gen_baking_systemd_unit(
                    requires,
                    f"Tezos baking instance for {network}",
                    [
                        f"/etc/default/tezos-baking-{network}",
                        f"/etc/default/tezos-node-{network}",
                    ],
                    "tezos-baking.conf",
                    network,
                )
            )
        custom_requires = ["tezos-node-custom@%i.service"]
        for network in target_networks:
            for proto in network_protos[network]:
                custom_requires.append(f"tezos-baker-{proto.lower()}@custom@%i.service")
        custom_unit = self.__gen_baking_systemd_unit(
            custom_requires,
            f"Tezos baking instance for custom network",
            [
                f"/etc/default/tezos-baking-custom@%i",
                f"/etc/default/tezos-node-custom@%i",
            ],
            "tezos-baking-custom.conf",
            "custom",
        )
        custom_unit.service_file.service.exec_stop_post.append(
            "/usr/bin/tezos-baking-custom-poststop %i"
        )
        custom_unit.instances = []
        self.systemd_units.append(custom_unit)
        self.postinst_steps = ""
        self.postrm_steps = ""

    def fetch_sources(self, out_dir, binaries_dir=None):
        os.makedirs(out_dir)
        package_dir = out_dir + "/tezos_baking"
        os.makedirs(package_dir)
        shutil.copy(f"{os.path.dirname(__file__)}/wizard_structure.py", package_dir)
        shutil.copy(f"{os.path.dirname(__file__)}/tezos_setup_wizard.py", package_dir)
        shutil.copy(f"{os.path.dirname(__file__)}/tezos_voting_wizard.py", package_dir)

    def gen_control_file(self, deps, ubuntu_version, out):
        run_deps_list = map(lambda x: x.lower(), self.additional_native_deps)
        run_deps = ", ".join(run_deps_list)
        file_contents = f"""
Source: {self.name}
Section: utils
Priority: optional
Maintainer: {self.meta.maintainer}
Build-Depends: debhelper (>=11), {"dh-systemd (>= 1.5), python3.8" if ubuntu_version != "jammy" else "python3-all"}, autotools-dev, dh-python, python3-setuptools
Standards-Version: 3.9.6
Homepage: https://gitlab.com/tezos/tezos/
X-Python3-Version: >= 3.8

Package: {self.name.lower()}
Architecture: amd64 arm64
Depends: ${{shlibs:Depends}}, ${{misc:Depends}}, {run_deps}, ${{python3:Depends}}{", python3.8" if ubuntu_version != "jammy" else ""}
Description: {self.desc}
"""
        with open(out, "w") as f:
            f.write(file_contents)

    def gen_spec_file(self, build_deps, run_deps, out):
        run_deps = ", ".join(self.additional_native_deps)
        (
            systemd_deps,
            systemd_install,
            systemd_files,
            systemd_macros,
        ) = gen_spec_systemd_part(self)
        version = self.meta.version.replace("-", "")
        file_contents = f"""
%define debug_package %{{nil}}
Name:    {self.name}
Version: {version}
Release: {self.meta.release}
Epoch: {self.meta.fedora_epoch}
Summary: {self.desc}
License: MIT
BuildArch: x86_64 aarch64
Source0: {self.name}-{version}.tar.gz
Source1: https://gitlab.com/tezos/tezos/tree/v{self.meta.version}/
BuildRequires: {systemd_deps}, python3-devel, python3-setuptools
Requires: {run_deps}
%description
{self.desc}
Maintainer: {self.meta.maintainer}
%prep
%autosetup -n {self.name}-{version}
%build
%py3_build
%install
%py3_install
{systemd_install}
%files
%{{_bindir}}/tezos-setup
%{{_bindir}}/tezos-vote
%{{python3_sitelib}}/tezos_baking-*.egg-info/
%{{python3_sitelib}}/tezos_baking/
%license LICENSE
{systemd_files}
{systemd_macros}
"""
        with open(out, "w") as f:
            f.write(file_contents)

    def gen_buildfile(self, out, ubuntu_version, binaries_dir=None):
        interpreter = "python3.8" if ubuntu_version != "jammy" else "python3"
        file_contents = f"""
from setuptools import setup

setup(
    name='tezos-baking',
    packages=['tezos_baking'],
    version='{self.meta.version}',
    entry_points=dict(
        console_scripts=[
            'tezos-setup=tezos_baking.tezos_setup_wizard:main',
            'tezos-vote=tezos_baking.tezos_voting_wizard:main',
        ]
    ),
    options=dict(
        build_scripts=dict(
            executable="/usr/bin/{interpreter}"
        ),
        console_scripts=dict(
            executable="/usr/bin/{interpreter}"
        )
    ),
)
"""
        with open(out, "w") as f:
            f.write(file_contents)

    def gen_rules(self, out, ubuntu_version, binaries_dir=None):
        rules_contents = gen_systemd_rules_contents(self, ubuntu_version)
        with open(out, "w") as f:
            f.write(rules_contents)

    def gen_license(self, out):
        shutil.copy(f"{os.path.dirname(__file__)}/../../LICENSE", out)

    def gen_postinst(self, out):
        postinst_contents = f"""#!/bin/sh

set -e

#DEBHELPER#

{self.postinst_steps}
"""
        postinst_contents = postinst_contents.replace(self.name, self.name.lower())
        with open(out, "w") as f:
            f.write(postinst_contents)
