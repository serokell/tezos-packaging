# SPDX-FileCopyrightText: 2020 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ

import os, subprocess
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
        startup_scripts = list(
            {
                x.startup_script
                for x in self.systemd_units
                if x.startup_script is not None
            }
        )
        prestart_scripts = list(
            {
                x.prestart_script
                for x in self.systemd_units
                if x.prestart_script is not None
            }
        )
        if len(startup_scripts + prestart_scripts) > 0:
            install_contents = "\n".join(
                [f"debian/{x} usr/bin" for x in startup_scripts + prestart_scripts]
            )
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
    startup_scripts = list({x.startup_script for x in systemd_units}) + list(
        {x.prestart_script for x in systemd_units}
    )
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
    for startup_script in startup_scripts:
        if startup_script is not None:
            install_startup_scripts += (
                f"install -m 0755 {startup_script} %{{buildroot}}/%{{_bindir}}\n"
            )
            systemd_startup_files += f"%{{_bindir}}/{startup_script}\n"
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

%:
	dh $@ {"--with systemd" if len(package.systemd_units) > 0 else ""}
override_dh_systemd_start:
	dh_systemd_start --no-start
{override_dh_install_init if len(package.systemd_units) > 1 else ""}"""
    return rules_contents


class OpamBasedPackage(AbstractPackage):
    def __init__(
        self,
        name: str,
        desc: str,
        meta: PackagesMeta,
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

    def fetch_sources(self, out_dir):
        opam_package = (
            "tezos-client" if self.name == "tezos-admin-client" else self.name
        )
        subprocess.run(
            ["opam", "exec", "--", "opam-bundle", f"{opam_package}={self.meta.version}"]
            + self.optional_opam_deps
            + ["--ocaml=4.10.2", "--yes", "--opam=2.0.8"],
            check=True,
        )
        subprocess.run(["tar", "-zxf", f"{opam_package}-bundle.tar.gz"], check=True)
        os.rename(f"{opam_package}-bundle", out_dir)

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

        file_contents = f"""
%define debug_package %{{nil}}
Name:    {self.name}
Version: {self.meta.version}
Release: {self.meta.release}
Epoch: {self.meta.fedora_epoch}
Summary: {self.desc}
License: MIT
BuildArch: x86_64 aarch64
Source0: {self.name}-{self.meta.version}.tar.gz
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
	./compile.sh
	cp $(CURDIR)/opam/default/bin/{self.name} {self.name}

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
        file_contents = f"""
%define debug_package %{{nil}}
Name:    {self.name}
Version: {self.meta.version}
Release: {self.meta.release}
Epoch: {self.meta.fedora_epoch}
Summary: {self.desc}
License: MIT
BuildArch: x86_64 aarch64
Source0: {self.name}-{self.meta.version}.tar.gz
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
    letter_version = "b"

    def __init__(
        self,
        target_networks: List[str],
        network_protos: Dict[str, List[str]],
        meta: PackagesMeta,
    ):
        self.name = "tezos-baking"
        self.desc = "Package that provides systemd services that orchestrate other services from Tezos packages"
        self.meta = deepcopy(meta)
        self.meta.version = self.meta.version + self.letter_version
        self.target_protos = set()
        for network in target_networks:
            for proto in network_protos[network]:
                self.target_protos.add(proto)
        self.systemd_units = []
        for network in target_networks:
            requires = [f"tezos-node-{network}.service"]
            for proto in network_protos[network]:
                requires.append(f"tezos-baker-{proto.lower()}@{network}.service")
                requires.append(f"tezos-endorser-{proto.lower()}@{network}.service")
            self.systemd_units.append(
                SystemdUnit(
                    service_file=ServiceFile(
                        Unit(
                            after=["network.target"],
                            requires=requires,
                            description=f"Tezos baking instance for {network}",
                        ),
                        Service(
                            exec_start="/usr/bin/tezos-baking-start",
                            user="tezos",
                            state_directory="tezos",
                            environment_file=f"/etc/default/tezos-baking-{network}",
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
                    suffix=network,
                    config_file="tezos-baking.conf",
                    startup_script="tezos-baking-start",
                    prestart_script="tezos-baking-prestart",
                )
            )
        self.postinst_steps = ""
        self.postrm_steps = ""

    def fetch_sources(self, out_dir):
        os.makedirs(out_dir)
        shutil.copy(f"{os.path.dirname(__file__)}/tezos_setup_wizard.py", out_dir)

    def gen_control_file(self, deps, ubuntu_version, out):
        run_deps = ", ".join(
            ["acl", "tezos-client", "tezos-node"]
            + sum(
                [
                    [
                        f"tezos-{daemon}-{proto.lower()}"
                        for daemon in ["baker", "endorser"]
                    ]
                    for proto in self.target_protos
                ],
                [],
            )
        )
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
        file_contents = f"""
%define debug_package %{{nil}}
Name:    {self.name}
Version: {self.meta.version}
Release: {self.meta.release}
Epoch: {self.meta.fedora_epoch}
Summary: {self.desc}
License: MIT
BuildArch: x86_64 aarch64
Source0: {self.name}-{self.meta.version}.tar.gz
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

install: tezos-baking tezos-setup-wizard
	mkdir -p $(DESTDIR)$(BINDIR)
	cp $(CURDIR)/tezos-setup-wizard $(DESTDIR)$(BINDIR)/tezos-setup-wizard
"""
        with open(out, "w") as f:
            f.write(file_contents)

    def gen_rules(self, out):
        rules_contents = gen_systemd_rules_contents(self)
        with open(out, "w") as f:
            f.write(rules_contents)

    def gen_license(self, out):
        shutil.copy(f"{os.path.dirname(__file__)}/../../LICENSE", out)
