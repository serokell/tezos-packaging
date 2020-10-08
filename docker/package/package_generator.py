#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2020 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: MPL-2.0

import os, shutil, sys, subprocess, json
from distutils.dir_util import copy_tree
from systemd_files_generator import gen_service, print_service_file

class Package:
    def __init__(self, name, desc, systemd_unit=None, target_proto=None, optional_opam_deps=[]):
        self.name = name
        self.desc = desc
        self.systemd_unit = systemd_unit
        self.target_proto = target_proto
        self.optional_opam_deps = optional_opam_deps

    def get_full_name(self):
        return self.name if self.target_proto is None else f"{self.name}-{self.target_proto}"

class SystemdUnit:
    def __init__(self, name, startup_script, config_file):
        self.name = name
        self.startup_script = startup_script
        self.config_file = config_file

if sys.argv[1] == "ubuntu":
    is_ubuntu = True
elif sys.argv[1] == "fedora":
    is_ubuntu = False
else:
    raise Exception(f"Unexpected package target OS, only 'ubuntu' and 'fedora' are supported.")

if sys.argv[2] == "source":
    is_source = True
elif sys.argv[2] == "binary":
    is_source = False
else:
    raise Exception("Unexpected package format, only 'source' and 'binary' are supported.")

package_to_build = None
if len(sys.argv) == 4:
    package_to_build = sys.argv[3]

date = subprocess.check_output(["date", "-R"]).decode().strip()
meta = json.load(open("../meta.json", "r"))

if is_ubuntu:
    run_deps = ["libev-dev", "libgmp-dev", "libhidapi-dev"]
else:
    run_deps = ["libev-devel", "gmp-devel", "hidapi-devel"]
build_deps = ["make", "m4", "perl", "pkg-config", "wget", "unzip", "rsync", "gcc"]
common_deps = run_deps + build_deps

active_protocols = json.load(open("../protocols.json", "r"))["active"]

version = os.environ["TEZOS_VERSION"][1:]
release = f"{meta['release']}"
package_version = f"{meta['epoch']}:0ubuntu{version}-{release}"

pwd = os.getcwd()
home = os.environ["HOME"]

def gen_control_file(pkg: Package, out):
    str_build_deps = ", ".join(build_deps)
    file_contents = f'''
Source: {pkg.get_full_name().lower()}
Section: utils
Priority: optional
Maintainer: {meta['maintainer']}
Build-Depends: debhelper (>=9), dh-systemd (>= 1.5), autotools-dev, {str_build_deps}
Standards-Version: 3.9.6
Homepage: https://gitlab.com/tezos/tezos/

Package: {pkg.get_full_name().lower()}
Architecture: amd64
Depends: ${{shlibs:Depends}}, ${{misc:Depends}}
Description: {pkg.desc}
'''
    with open(out, 'w') as f:
        f.write(file_contents)

def gen_spec_file(pkg: Package, out):
    full_package_name = package.name if package.target_proto is None else f"{package.name}-{package.target_proto}"
    build_requires = " ".join(build_deps + run_deps)
    requires = " ".join(run_deps)
    if pkg.systemd_unit is not None:
        systemd_deps = "systemd systemd-rpm-macros"
        systemd_install =f'''
mkdir -p %{{buildroot}}/%{{_unitdir}}
install -m 644 %{{name}}.service %{{buildroot}}/%{{_unitdir}}
mkdir -p %{{buildroot}}/%{{_sysconfdir}}/default
install -m 644 %{{name}}.default %{{buildroot}}/%{{_sysconfdir}}/default/%{{name}}
install -m 0755 {package.systemd_unit.startup_script} %{{buildroot}}/%{{_bindir}}
'''
        systemd_files =f'''
%{{_bindir}}/{package.systemd_unit.startup_script}
%{{_unitdir}}/%{{name}}.service
%{{_sysconfdir}}/default/%{{name}}
'''
        systemd_macros=f'''
%post
%systemd_post %{{name}}.service
useradd tezos -d /var/lib/tezos || true
systemctl enable %{{name}}.service

%preun
%systemd_preun %{{name}}.service

%postun
%systemd_postun_with_restart %{{name}}.service
'''
    else:
        systemd_deps = ""
        systemd_install = ""
        systemd_files = ""
        systemd_macros = ""

    file_contents = f'''
%define debug_package %{{nil}}
Name:    {full_package_name}
Version: {version}
Release: {release}
Epoch: 1
Summary: {pkg.desc}
License: MPL-2.0
BuildArch: x86_64
Source0: {full_package_name}-{version}.tar.gz
Source1: https://gitlab.com/tezos/tezos/tree/v{version}/
BuildRequires: {build_requires} {systemd_deps}
Requires: {requires}
%description
{pkg.desc}
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

def gen_makefile(pkg: Package, out):
    makefile_contents =f'''
.PHONY: install

BINDIR=/usr/bin

{pkg.get_full_name()}:
	./compile.sh
	cp $(CURDIR)/opam/default/bin/{pkg.get_full_name()} {pkg.get_full_name()}

install: {pkg.get_full_name()}
	mkdir -p $(DESTDIR)$(BINDIR)
	cp $(CURDIR)/{pkg.get_full_name()} $(DESTDIR)$(BINDIR)
'''
    with open(out, 'w') as f:
        f.write(makefile_contents)

def gen_changelog(pkg: Package, ubuntu_version, maintainer, date, out):
    changelog_contents = f'''{pkg.get_full_name().lower()} ({package_version}) {ubuntu_version}; urgency=medium

  * Publish {version}-{release} version of {pkg.name}

 -- {maintainer} {date}'''
    with open(out, 'w') as f:
        f.write(changelog_contents)

def gen_rules(out):
    rules_contents = f'''#!/usr/bin/make -f

%:
	dh $@ {"--with systemd" if package.systemd_unit is not None else ""}
override_dh_systemd_start:
	dh_systemd_start --no-start'''

    with open(out, 'w') as f:
        f.write(rules_contents)

def gen_install(pkg: Package, out):
    install_contents = f'''debian/{pkg.systemd_unit.startup_script} usr/bin
    '''
    with open(out, 'w') as f:
        f.write(install_contents)

packages = [
    Package("tezos-client",
            "CLI client for interacting with tezos blockchain",
            optional_opam_deps = ["tls", "ledgerwallet-tezos"]),
    Package("tezos-admin-client",
            "Administration tool for the node",
            optional_opam_deps = ["tls"]),
    Package("tezos-node",
            "Entry point for initializing, configuring and running a Tezos node",
            SystemdUnit("tezos-node.service", "tezos-node-start", "tezos-node.conf")
    ),
    Package("tezos-signer",
            "A client to remotely sign operations or blocks",
            optional_opam_deps = ["tls", "ledgerwallet-tezos"])
]

daemons = ["baker", "accuser", "endorser"]

daemon_decs = {
    "baker": "Daemon for baking",
    "accuser": "Daemon for accusing",
    "endorser": "Daemon for endorsing"
}

for protocol in active_protocols:
    for daemon in daemons:
        packages.append(
            Package(f"tezos-{daemon}",
                    daemon_decs[daemon],
                    SystemdUnit(f"tezos-{daemon}.service", f"tezos-{daemon}-start", f"tezos-{daemon}.conf"),
                    protocol,
                    optional_opam_deps = ["tls", "ledgerwallet-tezos"]
            )
        )

for package in packages:
    if package_to_build is None or package.get_full_name() == package_to_build:
        if is_ubuntu:
            dir = f"{package.get_full_name().lower()}-0ubuntu{version}"
        else:
            dir = f"{package.get_full_name()}-{version}"
        # tezos-client and tezos-admin-client are in one opam package
        opam_package = "tezos-client" if package.get_full_name() == "tezos-admin-client" else package.get_full_name()
        subprocess.run(["opam", "exec", "--", "opam-bundle", f"{opam_package}={version}"] + package.optional_opam_deps +
                       ["--ocaml=4.09.1", "--yes", "--opam=2.0.5"], check=True)
        subprocess.run(["tar", "-zxf", f"{opam_package}-bundle.tar.gz"], check=True)
        os.rename(f"{opam_package}-bundle", dir)
        gen_makefile(package, f"{dir}/Makefile")
        if not is_ubuntu:
            subprocess.run(["wget", "-q", "-O", f"{dir}/LICENSE", f"https://gitlab.com/tezos/tezos/-/raw/v{version}/LICENSE"], check=True)
        if is_ubuntu:
            subprocess.run(["tar", "-czf", f"{dir}.tar.gz", dir], check=True)
            os.chdir(dir)
            subprocess.run(["dh_make", "-syf" f"../{dir}.tar.gz"], check=True)
            if package.systemd_unit is not None:
                if package.target_proto is None:
                    service_file = gen_service(package.name)
                else:
                    service_file = gen_service(package.name, package.target_proto)
                service_file.service.environment_file = service_file.service.environment_file.lower()
                print_service_file(service_file, f"debian/{package.get_full_name().lower()}.service")
                shutil.copy(f"../defaults/{package.systemd_unit.config_file}", f"debian/{package.get_full_name().lower()}.default")
                shutil.copy(f"../scripts/{package.systemd_unit.startup_script}", f"debian/{package.systemd_unit.startup_script}")
                gen_install(package, "debian/install")
            gen_control_file(package, "debian/control")
            subprocess.run(["wget", "-q", "-O", "debian/copyright", f"https://gitlab.com/tezos/tezos/-/raw/v{version}/LICENSE"], check=True)
            subprocess.run("rm debian/*.ex debian/*.EX debian/README*", shell=True, check=True)
            gen_changelog(package, "bionic", meta["maintainer"], date, "debian/changelog")
            gen_rules("debian/rules")
            subprocess.run(["dpkg-buildpackage", "-S" if is_source else "-b", "-us", "-uc"],
                        check=True)
            os.chdir("..")
        else:
            if package.systemd_unit is not None:
                if package.target_proto is None:
                    service_file = gen_service(package.name)
                else:
                    service_file = gen_service(package.name, package.target_proto)
                print_service_file(service_file, f"{dir}/{package.get_full_name()}.service")
                shutil.copy(f"defaults/{package.systemd_unit.config_file}", f"{dir}/{package.get_full_name()}.default")
                shutil.copy(f"scripts/{package.systemd_unit.startup_script}", f"{dir}/{package.systemd_unit.startup_script}")
            subprocess.run(["tar", "-czf", f"{dir}.tar.gz", dir], check=True)
            os.makedirs(f"{home}/rpmbuild/SPECS", exist_ok=True)
            os.makedirs(f"{home}/rpmbuild/SOURCES", exist_ok=True)
            gen_spec_file(package, f"{home}/rpmbuild/SPECS/{package.get_full_name()}.spec")
            os.rename(f"{dir}.tar.gz", f"{home}/rpmbuild/SOURCES/{dir}.tar.gz")
            subprocess.run(["rpmbuild", "-bs" if is_source else "-bb", f"{home}/rpmbuild/SPECS/{package.get_full_name()}.spec"],
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
            os.rename(f"{artifacts_dir}/{f}", os.path.join("out", f))
