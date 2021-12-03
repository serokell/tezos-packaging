# SPDX-FileCopyrightText: 2020 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ

import os, subprocess
import re
import shutil
from copy import deepcopy
from abc import abstractmethod
from typing import List, Dict

from .meta import PackagesMeta
from .systemd import (
    Install,
    Service,
    ServiceFile,
    SystemdUnit,
    Unit,
)


class AbstractPackage:
    @abstractmethod
    def fetch_sources(self, out_dir):
        pass

    @abstractmethod
    def gen_control_file(self, out):
        pass

    @abstractmethod
    def get_spec_file(self, out):
        pass

    @abstractmethod
    def gen_makefile(self, out):
        pass

    def gen_changelog(self, ubuntu_version, maintainer, date, out):
        changelog_contents = f"""{self.name.lower()} ({self.meta.ubuntu_epoch}:{self.meta.version}-0ubuntu{self.meta.release}~{ubuntu_version}) {ubuntu_version}; urgency=medium

  * Publish {self.meta.version}-{self.meta.release} version of {self.name}

 -- {maintainer} {date}"""
        with open(out, "w") as f:
            f.write(changelog_contents)

    @abstractmethod
    def gen_rules(self, out):
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
        if len(scripts) > 0:
            install_contents = "\n".join([f"debian/{x} usr/bin" for x in scripts])
            with open(out, "w") as f:
                f.write(install_contents)

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
    default_files = ""
    for systemd_unit in package.systemd_units:
        if systemd_unit.suffix is None:
            service_name = "%{name}"
        else:
            service_name = f"%{{name}}-{systemd_unit.suffix}"
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


def gen_systemd_rules_contents(package):
    override_dh_install_init = "override_dh_installinit:\n"
    package_name = package.name.lower()
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
        override_dh_install_init += f"	dh_installinit --name={unit_name}\n"
    rules_contents = f"""#!/usr/bin/make -f

export DEB_CFLAGS_APPEND=-fPIC

%:
	dh $@ {"--with systemd" if len(package.systemd_units) > 0 else ""}
override_dh_systemd_start:
	dh_systemd_start --no-start
{override_dh_install_init if len(package.systemd_units) > 1 else ""}"""
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
        optional_opam_deps: List[str] = [],
        postinst_steps: str = "",
        postrm_steps: str = "",
        additional_native_deps: List[str] = [],
    ):
        self.name = name
        self.desc = desc
        self.systemd_units = systemd_units
        self.target_proto = target_proto
        self.optional_opam_deps = optional_opam_deps
        self.postinst_steps = postinst_steps
        self.postrm_steps = postrm_steps
        self.additional_native_deps = additional_native_deps
        self.meta = meta
        self.dune_filepath = dune_filepath

    def fetch_sources(self, out_dir):
        os.makedirs(out_dir)
        os.chdir(out_dir)
        shutil.copy(
            f"{os.path.dirname(__file__)}/scripts/build-binary.sh", "build-binary.sh"
        )
        subprocess.run(
            [
                "git",
                "clone",
                "--branch",
                f"v{self.meta.version}",
                "https://gitlab.com/tezos/tezos.git",
                "--depth",
                "1",
            ]
        )
        subprocess.run(["git", "clone", "https://gitlab.com/tezos/opam-repository.git"])
        with open("tezos/scripts/version.sh", "r") as f:
            opam_repository_tag = re.search(
                "^export opam_repository_tag=([0-9a-z]*)", f.read(), flags=re.MULTILINE
            ).group(1)
            os.chdir("opam-repository")
            subprocess.run(["git", "checkout", opam_repository_tag])
            subprocess.run(["rm", "-rf", ".git"])
            subprocess.run(["rm", "-r", "zcash-params"])
            subprocess.run(["opam", "admin", "cache"])
            os.chdir("../..")

    def gen_control_file(self, deps, ubuntu_version, out):
        str_build_deps = ", ".join(deps)
        str_additional_native_deps = ", ".join(self.additional_native_deps)
        file_contents = f"""
Source: {self.name.lower()}
Section: utils
Priority: optional
Maintainer: {self.meta.maintainer}
Build-Depends: debhelper (>=9), {"dh-systemd (>= 1.5), " if ubuntu_version != "hirsute" else ""} autotools-dev, {str_build_deps}
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
        build_requires = " ".join(build_deps)
        requires = " ".join(run_deps)
        str_additional_native_deps = ", ".join(self.additional_native_deps)
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
BuildRequires: {build_requires} {systemd_deps}
Requires: {requires}, {str_additional_native_deps}
%description
{self.desc}
Maintainer: {self.meta.maintainer}
%prep
%setup -q
%build
%install
make %{{name}}
mkdir -p %{{buildroot}}/%{{_bindir}}
install -m 0755 %{{name}} %{{buildroot}}/%{{_bindir}}
{systemd_install}
%files
%license LICENSE
%{{_bindir}}/%{{name}}
{systemd_files}
{systemd_macros}
"""
        with open(out, "w") as f:
            f.write(file_contents)

    def gen_makefile(self, out):
        makefile_contents = f"""
.PHONY: install

BINDIR=/usr/bin

{self.name}:
	./build-binary.sh {self.dune_filepath} {self.name}

install: {self.name}
	mkdir -p $(DESTDIR)$(BINDIR)
	cp $(CURDIR)/{self.name} $(DESTDIR)$(BINDIR)
"""
        with open(out, "w") as f:
            f.write(makefile_contents)

    def gen_rules(self, out):
        rules_contents = gen_systemd_rules_contents(self)
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
                f"https://gitlab.com/tezos/tezos/-/raw/v{self.meta.version}/LICENSE",
            ],
            check=True,
        )


class TezosSaplingParamsPackage(AbstractPackage):
    def __init__(self, meta: PackagesMeta):
        self.name = "tezos-sapling-params"
        self.desc = "Sapling params required in the runtime by the Tezos binaries"
        self.systemd_units = []
        self.targetProto = None
        self.meta = meta

    def fetch_sources(self, out_dir):
        os.makedirs(out_dir)
        subprocess.run(
            [
                "wget",
                "-P",
                out_dir,
                f"https://gitlab.com/tezos/opam-repository/-/raw/v{self.meta.version}/zcash-params/sapling-spend.params",
            ]
        )
        subprocess.run(
            [
                "wget",
                "-P",
                out_dir,
                f"https://gitlab.com/tezos/opam-repository/-/raw/v{self.meta.version}/zcash-params/sapling-output.params",
            ]
        )

    def gen_control_file(self, deps, ubuntu_version, out):
        file_contents = f"""
Source: {self.name}
Section: utils
Priority: optional
Maintainer: {self.meta.maintainer}
Build-Depends: debhelper (>=9), {"dh-systemd (>= 1.5), " if ubuntu_version != "hirsute" else ""} autotools-dev, wget
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

    def gen_makefile(self, out):
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

    def gen_rules(self, out):
        rules_contents = """#!/usr/bin/make -f

%:
	dh $@
"""
        with open(out, "w") as f:
            f.write(rules_contents)

    def gen_license(self, out):
        shutil.copy(f"{os.path.dirname(__file__)}/../../LICENSE", out)


class TezosBakingServicesPackage(AbstractPackage):

    # Sometimes we need to update the tezos-baking package inbetween
    # native releases, so we append an extra letter to the version of
    # the package.
    # This should be reset to "" whenever the native version is bumped.
    letter_version = ""

    def __gen_baking_systemd_unit(
        self, requires, description, environment_file, config_file, suffix
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
                    environment_file=environment_file,
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
        protocols: Dict[str, List[str]],
    ):
        self.name = "tezos-baking"
        self.desc = "Package that provides systemd services that orchestrate other services from Tezos packages"
        self.meta = deepcopy(meta)
        self.meta.version = self.meta.version + self.letter_version
        self.target_protos = set()
        self.noendorser_protos = protocols["active_noendorser"]
        for network in target_networks:
            for proto in network_protos[network]:
                self.target_protos.add(proto)
        self.systemd_units = []
        for network in target_networks:
            requires = [f"tezos-node-{network}.service"]
            for proto in network_protos[network]:
                requires.append(f"tezos-baker-{proto.lower()}@{network}.service")
                if proto not in self.noendorser_protos:
                    requires.append(f"tezos-endorser-{proto.lower()}@{network}.service")
            self.systemd_units.append(
                self.__gen_baking_systemd_unit(
                    requires,
                    f"Tezos baking instance for {network}",
                    f"/etc/default/tezos-baking-{network}",
                    "tezos-baking.conf",
                    network,
                )
            )
        custom_requires = []
        for network in target_networks:
            for proto in network_protos[network]:
                custom_requires.append(f"tezos-baker-{proto.lower()}@custom@%i.service")
                if proto not in self.noendorser_protos:
                    custom_requires.append(
                        f"tezos-endorser-{proto.lower()}@custom@%i.service"
                    )
        custom_unit = self.__gen_baking_systemd_unit(
            custom_requires,
            f"Tezos baking instance for custom network",
            f"/etc/default/tezos-baking-custom@%i",
            "tezos-baking-custom.conf",
            "custom",
        )
        custom_unit.service_file.service.exec_stop_post.append(
            "/usr/bin/tezos-baking-custom-poststop %i"
        )
        custom_unit.poststop_script = "tezos-baking-custom-poststop"
        custom_unit.instances = []
        self.systemd_units.append(custom_unit)
        self.postinst_steps = ""
        self.postrm_steps = ""

    def fetch_sources(self, out_dir):
        os.makedirs(out_dir)
        shutil.copy(f"{os.path.dirname(__file__)}/tezos_setup_wizard.py", out_dir)
        shutil.copy(f"{os.path.dirname(__file__)}/tezos_voting_wizard.py", out_dir)

    def gen_control_file(self, deps, ubuntu_version, out):
        run_deps_list = ["acl", "tezos-client", "tezos-node"]
        for proto in self.target_protos:
            run_deps_list.append(f"tezos-baker-{proto.lower()}")
            if proto not in self.noendorser_protos:
                run_deps_list.append(f"tezos-endorser-{proto.lower()}")
        run_deps = ", ".join(run_deps_list)
        file_contents = f"""
Source: {self.name}
Section: utils
Priority: optional
Maintainer: {self.meta.maintainer}
Build-Depends: debhelper (>=9), {"dh-systemd (>= 1.5), " if ubuntu_version != "hirsute" else ""} autotools-dev
Standards-Version: 3.9.6
Homepage: https://gitlab.com/tezos/tezos/

Package: {self.name.lower()}
Architecture: amd64 arm64
Depends: ${{shlibs:Depends}}, ${{misc:Depends}}, {run_deps}
Description: {self.desc}
"""
        with open(out, "w") as f:
            f.write(file_contents)

    def gen_spec_file(self, build_deps, run_deps, out):
        run_deps = ", ".join(
            ["acl", "tezos-client", "tezos-node"]
            + sum(
                [
                    [f"tezos-{daemon}-{proto}" for daemon in ["baker", "endorser"]]
                    for proto in self.target_protos
                ],
                [],
            )
        )
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
BuildRequires: {systemd_deps}
Requires: {run_deps}
%description
{self.desc}
Maintainer: {self.meta.maintainer}
%prep
%setup -q
%build
%install
mkdir -p %{{buildroot}}/%{{_bindir}}
{systemd_install}
%files
%license LICENSE
{systemd_files}
{systemd_macros}
"""
        with open(out, "w") as f:
            f.write(file_contents)

    def gen_makefile(self, out):
        file_contents = """
.PHONY: install

BINDIR=/usr/bin

tezos-baking:

tezos-setup-wizard:
	mv $(CURDIR)/tezos_setup_wizard.py $(CURDIR)/tezos-setup-wizard
	chmod +x $(CURDIR)/tezos-setup-wizard

tezos-voting-wizard:
	mv $(CURDIR)/tezos_voting_wizard.py $(CURDIR)/tezos-voting-wizard
	chmod +x $(CURDIR)/tezos-voting-wizard

install: tezos-baking tezos-setup-wizard tezos-voting-wizard
	mkdir -p $(DESTDIR)$(BINDIR)
	cp $(CURDIR)/tezos-setup-wizard $(DESTDIR)$(BINDIR)/tezos-setup-wizard
	cp $(CURDIR)/tezos-voting-wizard $(DESTDIR)$(BINDIR)/tezos-voting-wizard
"""
        with open(out, "w") as f:
            f.write(file_contents)

    def gen_rules(self, out):
        rules_contents = gen_systemd_rules_contents(self)
        with open(out, "w") as f:
            f.write(rules_contents)

    def gen_license(self, out):
        shutil.copy(f"{os.path.dirname(__file__)}/../../LICENSE", out)
