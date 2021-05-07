# SPDX-FileCopyrightText: 2020 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ

import os, shutil, sys, subprocess, json
from abc import ABCMeta, abstractmethod
from typing import List, Dict

# There are more possible fields, but only these are used by tezos services
class Service:
    def __init__(self, exec_start: str, state_directory:str, user: str,
                 exec_start_pre: str=None, exec_start_post: str=None,
                 exec_stop_post: str=None,
                 timeout_start_sec: str=None, environment_file: str=None, environment: List[str]=[],
                 remain_after_exit: bool=False, type_: str=None, restart: str=None,
                 keyring_mode: str=None):
        self.environment_file = environment_file
        self.environment = environment
        self.exec_start = exec_start
        self.exec_start_pre = exec_start_pre
        self.exec_start_post = exec_start_post
        self.exec_stop_post = exec_stop_post
        self.timeout_start_sec = timeout_start_sec
        self.state_directory = state_directory
        self.user = user
        self.remain_after_exit = remain_after_exit
        self.type_ = type_
        self.restart = restart
        self.keyring_mode = keyring_mode

class Unit:
    def __init__(self, after: List[str], description: str, requires: List[str]=[],
                 part_of: List[str]=[]):
        self.after = after
        self.requires = requires
        self.part_of = part_of
        self.description = description

class Install:
    def __init__(self, wanted_by: List[str]=[]):
        self.wanted_by = wanted_by

class ServiceFile:
    def __init__(self, unit: Unit, service:Service, install: Install):
        self.unit = unit
        self.service = service
        self.install = install

class SystemdUnit:
    def __init__(self, service_file:ServiceFile, startup_script:str=None,
                 startup_script_source:str=None,
                 prestart_script:str=None, prestart_script_source:str=None,
                 suffix:str=None, config_file: str=None, instances :List[str]=[]):
        self.suffix = suffix
        self.service_file = service_file
        self.startup_script = startup_script
        self.startup_script_source = startup_script_source
        self.prestart_script = prestart_script
        self.prestart_script_source = prestart_script_source
        self.config_file = config_file
        self.instances = instances

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

    @abstractmethod
    def gen_postinst(self, out):
        pass

    @abstractmethod
    def gen_postrm(self, out):
        pass


meta = json.load(open(f"{os.path.dirname(__file__)}/../../meta.json", "r"))
version = os.environ["TEZOS_VERSION"][1:]
release = f"{meta['release']}"
ubuntu_epoch = 2
fedora_epoch = 1


def gen_spec_systemd_part(package):
    systemd_units = package.systemd_units
    startup_scripts = list(set(map(lambda x: x.startup_script, package.systemd_units))) + \
        list(set(map(lambda x: x.prestart_script, package.systemd_units)))
    config_files = list(filter(lambda x: x is not None, map(lambda x: x.config_file,
                                                                package.systemd_units)))
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
    for systemd_unit in package.systemd_units:
        if systemd_unit.suffix is None:
            service_name = "%{name}"
        else:
            service_name = f"%{{name}}-{systemd_unit.suffix}"
        if len(systemd_unit.instances) > 0:
            service_name = f"{service_name}@"
        install_unit_files += f"install -m 644 {service_name}.service %{{buildroot}}/%{{_unitdir}}\n"
        systemd_unit_files += f"%{{_unitdir}}/{service_name}.service\n"
        if len(systemd_unit.instances) == 0:
            enable_units += f"systemctl enable {service_name}.service\n"
        systemd_units_post += f"%systemd_post {service_name}.service\n"
        systemd_units_preun += f"%systemd_preun {service_name}.service\n"
        systemd_units_postun += f"%systemd_postun_with_restart {service_name}.service\n"
        if systemd_unit.config_file is not None:
            install_default += f"install -m 644 {service_name}.default " + \
                f"%{{buildroot}}/%{{_sysconfdir}}/default/{service_name}\n"
            default_files += f"%{{_sysconfdir}}/default/{service_name}\n"
    install_startup_scripts = ""
    systemd_startup_files = ""
    for startup_script in startup_scripts:
        if startup_script is not None:
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
{enable_units}
{package.postinst_steps}

%preun
{systemd_units_preun}

%postun
{systemd_units_postun}
{package.postrm_steps}
'''
    return systemd_deps, systemd_install, systemd_files, systemd_macros

def gen_systemd_rules_contents(package):
    override_dh_install_init = "override_dh_installinit:\n"
    for systemd_unit in package.systemd_units:
        if len(systemd_unit.instances) == 0:
            if systemd_unit.suffix is not None:
                override_dh_install_init += f"	dh_installinit --name={package.name.lower()}-{systemd_unit.suffix}\n"
            else:
                override_dh_install_init += f"	dh_installinit --name={package.name.lower()}\n"
        else:
            if systemd_unit.suffix is not None:
                override_dh_install_init += f"	dh_installinit --name={package.name.lower()}-{systemd_unit.suffix}@\n"
            else:
                override_dh_install_init += f"	dh_installinit --name={package.name.lower()}@\n"
    rules_contents = f'''#!/usr/bin/make -f

%:
	dh $@ {"--with systemd" if len(package.systemd_units) > 0 else ""}
override_dh_systemd_start:
	dh_systemd_start --no-start
{override_dh_install_init if len(package.systemd_units) > 1 else ""}'''
    return rules_contents

class OpamBasedPackage(AbstractPackage):
    def __init__(self, name: str, desc: str, systemd_units: List[SystemdUnit]=[],
                 target_proto: str=None, optional_opam_deps: List[str]=[],
                 postinst_steps: str="", postrm_steps: str="",
                 additional_native_deps: List[str]=[]):
        self.name = name
        self.desc = desc
        self.systemd_units = systemd_units
        self.target_proto = target_proto
        self.optional_opam_deps = optional_opam_deps
        self.postinst_steps = postinst_steps
        self.postrm_steps = postrm_steps
        self.additional_native_deps = additional_native_deps

    def fetch_sources(self, out_dir):
        opam_package = "tezos-client" if self.name == "tezos-admin-client" else self.name
        subprocess.run(["opam", "exec", "--", "opam-bundle", f"{opam_package}={version}"] + self.optional_opam_deps +
                       ["--ocaml=4.10.2", "--yes", "--opam=2.0.8"], check=True)
        subprocess.run(["tar", "-zxf", f"{opam_package}-bundle.tar.gz"], check=True)
        os.rename(f"{opam_package}-bundle", out_dir)


    def gen_control_file(self, deps, out):
        str_build_deps = ", ".join(deps)
        str_additional_native_deps = ", ".join(self.additional_native_deps)
        file_contents = f'''
Source: {self.name.lower()}
Section: utils
Priority: optional
Maintainer: {meta['maintainer']}
Build-Depends: debhelper (>=9), dh-systemd (>= 1.5), autotools-dev, {str_build_deps}
Standards-Version: 3.9.6
Homepage: https://gitlab.com/tezos/tezos/

Package: {self.name.lower()}
Architecture: amd64 arm64
Depends: ${{shlibs:Depends}}, ${{misc:Depends}}, {str_additional_native_deps}
Description: {self.desc}
'''
        with open(out, 'w') as f:
            f.write(file_contents)

    def gen_spec_file(self, build_deps, run_deps, out):
        build_requires = " ".join(build_deps)
        config_files = list(filter(lambda x: x is not None, map(lambda x: x.config_file,
                                                                self.systemd_units)))
        requires = " ".join(run_deps)
        str_additional_native_deps = ", ".join(self.additional_native_deps)
        systemd_deps, systemd_install, systemd_files, systemd_macros = \
            gen_spec_systemd_part(self)

        file_contents = f'''
%define debug_package %{{nil}}
Name:    {self.name}
Version: {version}
Release: {release}
Epoch: {fedora_epoch}
Summary: {self.desc}
License: MIT
BuildArch: x86_64 aarch64
Source0: {self.name}-{version}.tar.gz
Source1: https://gitlab.com/tezos/tezos/tree/v{version}/
BuildRequires: {build_requires} {systemd_deps}
Requires: {requires}, {str_additional_native_deps}
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
        rules_contents = gen_systemd_rules_contents(self)
        with open(out, 'w') as f:
            f.write(rules_contents)

    def gen_install(self, out):
        startup_scripts = \
            list({x.startup_script for x in self.systemd_units if x.startup_script is not None})
        prestart_scripts = \
            list({x.prestart_script for x in self.systemd_units if x.prestart_script is not None})
        install_contents = "\n".join(map(lambda x: f"debian/{x} usr/bin",
                                         startup_scripts + prestart_scripts))
        with open(out, 'w') as f:
            f.write(install_contents)

    def gen_postinst(self, out):
        postinst_contents = f'''#!/bin/sh

set -e

#DEBHELPER#

{self.postinst_steps}
'''
        postinst_contents = postinst_contents.replace(self.name, self.name.lower())
        with open(out, 'w') as f:
            f.write(postinst_contents)

    def gen_postrm(self, out):
        postrm_contents = f'''#!/bin/sh

set -e

#DEBHELPER#

{self.postrm_steps}
'''
        postrm_contents = postrm_contents.replace(self.name, self.name.lower())
        with open(out, 'w') as f:
            f.write(postrm_contents)

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
Architecture: amd64 arm64
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
BuildArch: x86_64 aarch64
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
    part_of = "".join(map(lambda x: f"PartOf={x}\n", service_file.unit.part_of))
    environment = "".join(map(lambda x: f"Environment=\"{x}\"\n", service_file.service.environment))
    environment_file = "" if service_file.service.environment_file is None else f"EnvironmentFile={service_file.service.environment_file}"
    wanted_by = "".join(map(lambda x: f"WantedBy=\"{x}\"\n", service_file.install.wanted_by))
    exec_start_pres = \
        "\n".join(f"ExecStartPre={x}" for x in service_file.service.exec_start_pre) \
            if service_file.service.exec_start_pre is not None else ""
    exec_start_posts = \
        "\n".join(f"ExecStartPost={x}" for x in service_file.service.exec_start_post) \
            if service_file.service.exec_start_post is not None else ""
    exec_stop_posts = \
        "\n".join(f"ExecStopPost={x}" for x in service_file.service.exec_stop_post) \
            if service_file.service.exec_stop_post is not None else ""
    file_contents = f'''# SPDX-FileCopyrightText: 2020 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ
[Unit]
{after}{requires}{part_of}Description={service_file.unit.description}
[Service]
{environment_file}
{environment}
{exec_start_pres}
{f"TimeoutStartSec={service_file.service.timeout_start_sec}" if service_file.service.timeout_start_sec is not None else ""}
ExecStart={service_file.service.exec_start}
{exec_start_posts}
{exec_stop_posts}
StateDirectory={service_file.service.state_directory}
User={service_file.service.user}
Group={service_file.service.user}
{"RemainAfterExit=yes" if service_file.service.remain_after_exit else ""}
{f"Type={service_file.service.type_}" if service_file.service.type_ is not None else ""}
{f"Restart={service_file.service.restart}" if service_file.service.restart is not None else ""}
{f"KeyringMode={service_file.service.keyring_mode}" if service_file.service.keyring_mode is not None else ""}
[Install]
{wanted_by}
'''
    with open(out, 'w') as f:
        f.write(file_contents)


class TezosBakingServicesPackage(AbstractPackage):
    def __init__(self, target_networks: List[str], network_protos: Dict[str, List[str]]):
        self.name = "tezos-baking"
        self.desc = \
            "Package that provides systemd services that orchestrate other services from Tezos packages"
        self.target_protos = set()
        for network in target_networks:
            for proto in network_protos[network]:
                self.target_protos.add(proto)
        self.systemd_units = []
        for network in target_networks:
            self.systemd_units.append(
                SystemdUnit(
                    service_file=ServiceFile(
                        Unit(after=["network.target"],
                             description=f"Tezos baking instance for {network}"),
                        Service(exec_start="/usr/bin/tezos-baking-start", user="tezos", state_directory="tezos",
                                environment_file=f"/etc/default/tezos-baking-{network}",
                                exec_start_pre=["+/usr/bin/setfacl -m u:tezos:rwx /run/systemd/ask-password",
                                                "/usr/bin/tezos-baking-prestart"],
                                exec_stop_post=["+/usr/bin/setfacl -x u:tezos /run/systemd/ask-password"],
                                remain_after_exit=True, type_="oneshot", keyring_mode="shared"),
                        Install(wanted_by=["multi-user.target"])
                    ),
                    suffix=network,
                    config_file="tezos-baking.conf",
                    startup_script="tezos-baking-start",
                    prestart_script="tezos-baking-prestart"
                )
            )
        self.postinst_steps = ""
        self.postrm_steps = ""
    def fetch_sources(self, out_dir):
        os.makedirs(out_dir)

    def gen_control_file(self, deps, out):
        run_deps = ", ".join(["acl", "tezos-client", "tezos-node"] + \
            sum([[f"tezos-{daemon}-{proto.lower()}" for daemon in ["baker", "endorser"]] for proto in self.target_protos],
                []))
        file_contents = f'''
Source: {self.name}
Section: utils
Priority: optional
Maintainer: {meta['maintainer']}
Build-Depends: debhelper (>=9), dh-systemd (>= 1.5), autotools-dev
Standards-Version: 3.9.6
Homepage: https://gitlab.com/tezos/tezos/

Package: {self.name.lower()}
Architecture: amd64 arm64
Depends: ${{shlibs:Depends}}, ${{misc:Depends}}, {run_deps}
Description: {self.desc}
'''
        with open(out, 'w') as f:
            f.write(file_contents)

    def gen_spec_file(self, build_deps, run_deps, out):
        run_deps = ", ".join(["acl", "tezos-client", "tezos-node"] + \
            sum([[f"tezos-{daemon}-{proto}" for daemon in ["baker", "endorser"]] for proto in self.target_protos],
                []))
        systemd_deps, systemd_install, systemd_files, systemd_macros = \
            gen_spec_systemd_part(self)
        file_contents = f'''
%define debug_package %{{nil}}
Name:    {self.name}
Version: {version}
Release: {release}
Epoch: {fedora_epoch}
Summary: {self.desc}
License: MIT
BuildArch: x86_64 aarch64
Source0: {self.name}-{version}.tar.gz
Source1: https://gitlab.com/tezos/tezos/tree/v{version}/
BuildRequires: {systemd_deps}
Requires: {run_deps}
%description
{self.desc}
Maintainer: {meta['maintainer']}
%prep
%setup -q
%build
%install
{systemd_install}
%files
%license LICENSE
{systemd_files}
{systemd_macros}
'''
        with open(out, 'w') as f:
            f.write(file_contents)

    def gen_makefile(self, out):
        file_contents = '''
.PHONY: install

tezos-baking:

install: tezos-baking
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
        rules_contents = gen_systemd_rules_contents(self)
        with open(out, 'w') as f:
            f.write(rules_contents)

    def gen_install(self, out):
        startup_scripts = \
            list({x.startup_script for x in self.systemd_units if x.startup_script is not None})
        prestart_scripts = \
            list({x.prestart_script for x in self.systemd_units if x.prestart_script is not None})
        install_contents = "\n".join(map(lambda x: f"debian/{x} usr/bin",
                                         startup_scripts + prestart_scripts))
        with open(out, 'w') as f:
            f.write(install_contents)
