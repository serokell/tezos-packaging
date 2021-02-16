# SPDX-FileCopyrightText: 2020 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ

import os, shutil, sys, subprocess, json
from abc import ABCMeta, abstractmethod
from typing import List

# There are more possible fields, but only these are used by tezos services
class Service:
    def __init__(self, exec_start: str, state_directory:str, user: str,
                 environment_file: str=None, environment: List[str]=[]):
        self.environment_file = environment_file
        self.environment = environment
        self.exec_start = exec_start
        self.state_directory = state_directory
        self.user = user

class Unit:
    def __init__(self, after: List[str], description: str, requires: List[str]=[]):
        self.after = after
        self.requires = requires
        self.description = description

class ServiceFile:
    def __init__(self, unit: Unit, service:Service):
        self.unit = unit
        self.service = service

class SystemdUnit:
    def __init__(self, service_file:ServiceFile, startup_script:str, suffix:str=None,
                 config_file: str=None):
        self.suffix = suffix
        self.service_file = service_file
        self.startup_script = startup_script
        self.config_file = config_file

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

    @abstractmethod
    def gen_changelog(self, out):
        pass

    @abstractmethod
    def gen_rules(self, out):
        pass

    @abstractmethod
    def gen_install(self, out):
        pass


meta = json.load(open(f"{os.path.dirname(__file__)}/../../meta.json", "r"))
version = os.environ["TEZOS_VERSION"][1:]
release = f"{meta['release']}"
ubuntu_epoch = 2
fedora_epoch = 1


class OpamBasedPackage(AbstractPackage):
    def __init__(self, name: str, desc: str, systemd_units: List[SystemdUnit]=[],
                 target_proto: str=None, optional_opam_deps: List[str]=[],
                 requires_sapling_params: bool=False):
        self.name = name
        self.desc = desc
        self.systemd_units = systemd_units
        self.target_proto = target_proto
        self.optional_opam_deps = optional_opam_deps
        self.requires_sapling_params = requires_sapling_params

    def fetch_sources(self, out_dir):
        opam_package = "tezos-client" if self.name == "tezos-admin-client" else self.name
        subprocess.run(["opam", "exec", "--", "opam-bundle", f"{opam_package}={version}"] + self.optional_opam_deps +
                       ["--ocaml=4.09.1", "--yes", "--opam=2.0.5"], check=True)
        subprocess.run(["tar", "-zxf", f"{opam_package}-bundle.tar.gz"], check=True)
        os.rename(f"{opam_package}-bundle", out_dir)


    def gen_control_file(self, deps, out):
        str_build_deps = ", ".join(deps)
        file_contents = f'''
Source: {self.name.lower()}
Section: utils
Priority: optional
Maintainer: {meta['maintainer']}
Build-Depends: debhelper (>=9), dh-systemd (>= 1.5), autotools-dev, {str_build_deps}
Standards-Version: 3.9.6
Homepage: https://gitlab.com/tezos/tezos/

Package: {self.name.lower()}
Architecture: amd64
Depends: ${{shlibs:Depends}}, ${{misc:Depends}}, {"tezos-sapling-params" if self.requires_sapling_params else ""}
Description: {self.desc}
'''
        with open(out, 'w') as f:
            f.write(file_contents)

    def gen_spec_file(self, build_deps, run_deps, out):
        build_requires = " ".join(build_deps)
        config_files = list(filter(lambda x: x is not None, map(lambda x: x.config_file,
                                                                self.systemd_units)))
        requires = " ".join(run_deps)
        if len(self.systemd_units) > 0:
            startup_scripts = list(set(map(lambda x: x.startup_script, self.systemd_units)))
            install_unit_files = ""
            systemd_unit_files = ""
            enable_units = ""
            systemd_units_post = ""
            systemd_units_preun = ""
            systemd_units_postun = ""
            if len(config_files) > 0:
                install_default = f"mkdir -p %{{buildroot}}/%{{_sysconfdir}}/default\n"
            else:
                install_default = ""
            default_files = ""
            for systemd_unit in self.systemd_units:
                if systemd_unit.suffix is None:
                    install_unit_files += f"install -m 644 %{{name}}.service %{{buildroot}}/%{{_unitdir}}\n"
                    systemd_unit_files += f"%{{_unitdir}}/%{{name}}.service\n"
                    enable_units += f"systemctl enable %{{name}}.service\n"
                    systemd_units_post += f"%systemd_post %{{name}}.service\n"
                    systemd_units_preun += f"%systemd_preun %{{name}}.service\n"
                    systemd_units_postun += f"%systemd_postun_with_restart %{{name}}.service\n"
                    if systemd_unit.config_file is not None:
                        install_default += f"install -m 644 %{{name}}.default " + \
                            f"%{{buildroot}}/%{{_sysconfdir}}/default/%{{name}}\n"
                        default_files += f"%{{_sysconfdir}}/default/%{{name}}\n"
                else:
                    install_unit_files += f"install -m 644 %{{name}}-{systemd_unit.suffix}.service %{{buildroot}}/%{{_unitdir}}\n"
                    systemd_unit_files += f"%{{_unitdir}}/%{{name}}-{systemd_unit.suffix}.service\n"
                    enable_units += f"systemctl enable %{{name}}-{systemd_unit.suffix}.service\n"
                    systemd_units_post += f"%systemd_post %{{name}}-{systemd_unit.suffix}.service\n"
                    systemd_units_preun += f"%systemd_preun %{{name}}-{systemd_unit.suffix}.service\n"
                    systemd_units_postun += f"%systemd_postun_with_restart %{{name}}-{systemd_unit.suffix}.service\n"
                    if systemd_unit.config_file is not None:
                        install_default += f"install -m 644 %{{name}}-{systemd_unit.suffix}.default " + \
                            f"%{{buildroot}}/%{{_sysconfdir}}/default/%{{name}}-{systemd_unit.suffix}\n"
                        default_files += f"%{{_sysconfdir}}/default/%{{name}}-{systemd_unit.suffix}\n"
            install_startup_scripts = ""
            systemd_startup_files = ""
            for startup_script in startup_scripts:
                install_startup_scripts += f"install -m 0755 {startup_script} %{{buildroot}}/%{{_bindir}}\n"
                systemd_startup_files += f"%{{_bindir}}/{startup_script}\n"
            systemd_deps = "systemd systemd-rpm-macros"
            systemd_install = f'''
mkdir -p %{{buildroot}}/%{{_unitdir}}
{install_unit_files}
{install_default}
{install_startup_scripts}
'''
            systemd_files = f'''
{systemd_startup_files}
{systemd_unit_files}
{default_files}
'''
            systemd_macros= f'''
%post
{systemd_units_post}
useradd tezos -d /var/lib/tezos || true
{enable_units}

%preun
{systemd_units_preun}

%postun
{systemd_units_postun}
'''
        else:
            systemd_deps = ""
            systemd_install = ""
            systemd_files = ""
            systemd_macros = ""

        file_contents = f'''
%define debug_package %{{nil}}
Name:    {self.name}
Version: {version}
Release: {release}
Epoch: {fedora_epoch}
Summary: {self.desc}
License: MIT
BuildArch: x86_64
Source0: {self.name}-{version}.tar.gz
Source1: https://gitlab.com/tezos/tezos/tree/v{version}/
BuildRequires: {build_requires} {systemd_deps}
Requires: {requires}, {"tezos-sapling-params" if self.requires_sapling_params else ""}
%description
{self.desc}
Maintainer: {meta['maintainer']}
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
'''
        with open(out, 'w') as f:
            f.write(file_contents)

    def gen_makefile(self, out):
        makefile_contents =f'''
.PHONY: install

BINDIR=/usr/bin

{self.name}:
	./compile.sh
	cp $(CURDIR)/opam/default/bin/{self.name} {self.name}

install: {self.name}
	mkdir -p $(DESTDIR)$(BINDIR)
	cp $(CURDIR)/{self.name} $(DESTDIR)$(BINDIR)
'''
        with open(out, 'w') as f:
            f.write(makefile_contents)

    def gen_changelog(self, ubuntu_version, maintainer, date, out):
        changelog_contents = f'''{self.name.lower()} ({ubuntu_epoch}:{version}-0ubuntu{release}~{ubuntu_version}) {ubuntu_version}; urgency=medium

  * Publish {version}-{release} version of {self.name}

 -- {maintainer} {date}'''
        with open(out, 'w') as f:
            f.write(changelog_contents)

    def gen_rules(self, out):
        override_dh_install_init = "override_dh_installinit:\n"
        for systemd_unit in self.systemd_units:
            if systemd_unit.suffix is not None:
                override_dh_install_init += f"	dh_installinit --name={self.name}-{systemd_unit.suffix}\n"
        rules_contents = f'''#!/usr/bin/make -f

%:
	dh $@ {"--with systemd" if len(self.systemd_units) > 0 else ""}
override_dh_systemd_start:
	dh_systemd_start --no-start
{override_dh_install_init if len(self.systemd_units) > 1 else ""}'''
        with open(out, 'w') as f:
            f.write(rules_contents)

    def gen_install(self, out):
        startup_scripts = list(set(map(lambda x: x.startup_script, self.systemd_units)))
        install_contents = "\n".join(map(lambda x: f"debian/{x} usr/bin",
                                         startup_scripts))
        with open(out, 'w') as f:
            f.write(install_contents)


class TezosSaplingParamsPackage(AbstractPackage):
    def __init__(self):
        self.name = "tezos-sapling-params"
        self.desc = "Sapling params required in the runtime by the Tezos binaries"
        self.systemd_units = []
        self.targetProto = None

    def fetch_sources(self, out_dir):
        os.makedirs(out_dir)
        subprocess.run(["wget", "-P", out_dir, f"https://gitlab.com/tezos/opam-repository/-/raw/v{version}/zcash-params/sapling-spend.params"])
        subprocess.run(["wget", "-P", out_dir, f"https://gitlab.com/tezos/opam-repository/-/raw/v{version}/zcash-params/sapling-output.params"])

    def gen_control_file(self, deps, out):
        file_contents = f'''
Source: {self.name}
Section: utils
Priority: optional
Maintainer: {meta['maintainer']}
Build-Depends: debhelper (>=9), dh-systemd (>= 1.5), autotools-dev, wget
Standards-Version: 3.9.6
Homepage: https://gitlab.com/tezos/tezos/

Package: {self.name.lower()}
Architecture: amd64
Depends: ${{shlibs:Depends}}, ${{misc:Depends}}
Description: {self.desc}
'''
        with open(out, 'w') as f:
            f.write(file_contents)

    def gen_spec_file(self, build_deps, run_deps, out):
        file_contents = f'''
%define debug_package %{{nil}}
Name:    {self.name}
Version: {version}
Release: {release}
Epoch: {fedora_epoch}
Summary: {self.desc}
License: MIT
BuildArch: x86_64
Source0: {self.name}-{version}.tar.gz
BuildRequires: wget
%description
{self.desc}
Maintainer: {meta['maintainer']}
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
'''
        with open(out, 'w') as f:
            f.write(file_contents)

    def gen_makefile(self, out):
        file_contents = '''
.PHONY: install

DATADIR=/usr/share/zcash-params/

tezos-sapling-params:

install: tezos-sapling-params
	mkdir -p $(DESTDIR)$(DATADIR)
	cp $(CURDIR)/sapling-spend.params $(DESTDIR)$(DATADIR)
	cp $(CURDIR)/sapling-output.params $(DESTDIR)$(DATADIR)
'''
        with open(out, 'w') as f:
            f.write(file_contents)

    def gen_changelog(self, ubuntu_version, maintainer, date, out):
        changelog_contents = f'''{self.name.lower()} ({ubuntu_epoch}:{version}-0ubuntu{release}~{ubuntu_version}) {ubuntu_version}; urgency=medium

  * Publish {version}-{release} version of {self.name}

 -- {maintainer} {date}'''
        with open(out, 'w') as f:
            f.write(changelog_contents)

    def gen_rules(self, out):
        rules_contents = '''#!/usr/bin/make -f

%:
	dh $@
'''
        with open(out, 'w') as f:
            f.write(rules_contents)


def print_service_file(service_file: ServiceFile, out):
    after = "".join(map(lambda x: f"After={x}\n", service_file.unit.after))
    requires = "".join(map(lambda x: f"Requires={x}\n", service_file.unit.requires))
    environment = "".join(map(lambda x: f"Environment=\"{x}\"\n", service_file.service.environment))
    environment_file = "" if service_file.service.environment_file is None else f"EnvironmentFile={service_file.service.environment_file}"
    file_contents = f'''# SPDX-FileCopyrightText: 2020 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ
[Unit]
{after}{requires}Description={service_file.unit.description}
[Service]
{environment_file}
{environment}ExecStart={service_file.service.exec_start}
StateDirectory={service_file.service.state_directory}
User={service_file.service.user}
Group={service_file.service.user}
[Install]
WantedBy=multi-user.target
'''
    with open(out, 'w') as f:
        f.write(file_contents)
