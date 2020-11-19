# SPDX-FileCopyrightText: 2020 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ

import os, shutil, sys, subprocess, json
from distutils.dir_util import copy_tree

from .model import Package, print_service_file
from .packages import packages

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
meta = json.load(open(f"{os.path.dirname(__file__)}/../../meta.json", "r"))

if is_ubuntu:
    run_deps = ["libev-dev", "libgmp-dev", "libhidapi-dev"]
else:
    run_deps = ["libev-devel", "gmp-devel", "hidapi-devel"]
build_deps = ["make", "m4", "perl", "pkg-config", "wget", "unzip", "rsync", "gcc"]
common_deps = run_deps + build_deps

active_protocols = json.load(open(f"{os.path.dirname(__file__)}/../../protocols.json", "r"))["active"]

version = os.environ["TEZOS_VERSION"][1:]
release = f"{meta['release']}"

ubuntu_epoch = 2
fedora_epoch = 1

pwd = os.getcwd()
home = os.environ["HOME"]

def gen_control_file(pkg: Package, out):
    str_build_deps = ", ".join(build_deps)
    file_contents = f'''
Source: {pkg.name.lower()}
Section: utils
Priority: optional
Maintainer: {meta['maintainer']}
Build-Depends: debhelper (>=9), dh-systemd (>= 1.5), autotools-dev, {str_build_deps}
Standards-Version: 3.9.6
Homepage: https://gitlab.com/tezos/tezos/

Package: {pkg.name.lower()}
Architecture: amd64
Depends: ${{shlibs:Depends}}, ${{misc:Depends}}
Description: {pkg.desc}
'''
    with open(out, 'w') as f:
        f.write(file_contents)

def gen_spec_file(pkg: Package, out):
    build_requires = " ".join(build_deps + run_deps)
    config_files = list(filter(lambda x: x is not None, map(lambda x: x.config_file, package.systemd_units)))
    requires = " ".join(run_deps)
    if len(pkg.systemd_units) > 0:
        startup_scripts = list(set(map(lambda x: x.startup_script, pkg.systemd_units)))
        install_unit_files = ""
        systemd_unit_files = ""
        enable_units = ""
        systemd_units_post = ""
        systemd_units_preun = ""
        systemd_units_postun = ""
        if len(config_files) == 1:
            install_default = f'''
mkdir -p %{{buildroot}}/%{{_sysconfdir}}/default
install -m 644 %{{name}}.default %{{buildroot}}/%{{_sysconfdir}}/default/%{{name}}'''
        else:
            install_default = ""
        for systemd_unit in pkg.systemd_units:
            if systemd_unit.suffix is None:
                install_unit_files += f"install -m 644 %{{name}}.service %{{buildroot}}/%{{_unitdir}}\n"
                systemd_unit_files += f"%{{_unitdir}}/%{{name}}.service\n"
                enable_units += f"systemctl enable %{{name}}.service\n"
                systemd_units_post += f"%systemd_post %{{name}}.service\n"
                systemd_units_preun += f"%systemd_preun %{{name}}.service\n"
                systemd_units_postun += f"%systemd_postun_with_restart %{{name}}.service\n"
            else:
                install_unit_files += f"install -m 644 %{{name}}-{systemd_unit.suffix}.service %{{buildroot}}/%{{_unitdir}}\n"
                systemd_unit_files += f"%{{_unitdir}}/%{{name}}-{systemd_unit.suffix}.service\n"
                enable_units += f"systemctl enable %{{name}}-{systemd_unit.suffix}.service\n"
                systemd_units_post += f"%systemd_post %{{name}}-{systemd_unit.suffix}.service\n"
                systemd_units_preun += f"%systemd_preun %{{name}}-{systemd_unit.suffix}.service\n"
                systemd_units_postun += f"%systemd_postun_with_restart %{{name}}-{systemd_unit.suffix}.service\n"
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
{ f"%{{_sysconfdir}}/default/%{{name}}" if len(config_files) == 1 else "" }
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
Name:    {pkg.name}
Version: {version}
Release: {release}
Epoch: {fedora_epoch}
Summary: {pkg.desc}
License: MIT
BuildArch: x86_64
Source0: {pkg.name}-{version}.tar.gz
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

{pkg.name}:
	./compile.sh
	cp $(CURDIR)/opam/default/bin/{pkg.name} {pkg.name}

install: {pkg.name}
	mkdir -p $(DESTDIR)$(BINDIR)
	cp $(CURDIR)/{pkg.name} $(DESTDIR)$(BINDIR)
'''
    with open(out, 'w') as f:
        f.write(makefile_contents)

def gen_changelog(pkg: Package, ubuntu_version, maintainer, date, out):
    changelog_contents = f'''{pkg.name.lower()} ({ubuntu_epoch}:{version}-0ubuntu{release}) {ubuntu_version}; urgency=medium

  * Publish {version}-{release} version of {pkg.name}

 -- {maintainer} {date}'''
    with open(out, 'w') as f:
        f.write(changelog_contents)

def gen_rules(pkg: Package, out):
    override_dh_install_init = "override_dh_installinit:\n"
    for systemd_unit in pkg.systemd_units:
        if systemd_unit.suffix is not None:
            override_dh_install_init += f"	dh_installinit --name={pkg.name}-{systemd_unit.suffix}\n"
    rules_contents = f'''#!/usr/bin/make -f

%:
	dh $@ {"--with systemd" if len(pkg.systemd_units) > 0 else ""}
override_dh_systemd_start:
	dh_systemd_start --no-start
{override_dh_install_init if len(pkg.systemd_units) > 1 else ""}'''

    with open(out, 'w') as f:
        f.write(rules_contents)

def gen_install(pkg: Package, out):
    startup_scripts = list(set(map(lambda x: x.startup_script, pkg.systemd_units)))
    install_contents = "\n".join(map(lambda x: f"debian/{x} usr/bin",
                                     startup_scripts))
    with open(out, 'w') as f:
        f.write(install_contents)

for package in packages:
    if package_to_build is None or package.name == package_to_build:
        if is_ubuntu:
            dir = f"{package.name.lower()}-{version}"
        else:
            dir = f"{package.name}-{version}"
        # tezos-client and tezos-admin-client are in one opam package

        opam_package = "tezos-client" if package.name == "tezos-admin-client" else package.name
        subprocess.run(["opam", "exec", "--", "opam-bundle", f"{opam_package}={version}"] + package.optional_opam_deps +
                        ["--ocaml=4.09.1", "--yes", "--opam=2.0.5"], check=True)
        subprocess.run(["tar", "-zxf", f"{opam_package}-bundle.tar.gz"], check=True)
        os.rename(f"{opam_package}-bundle", dir)
        # subprocess.run(["mkdir", dir])
        gen_makefile(package, f"{dir}/Makefile")
        config_files = list(filter(lambda x: x is not None, map(lambda x: x.config_file, package.systemd_units)))
        if len(config_files) > 1:
            raise Exception("Packages cannot have more than one default config file for package")
        if not is_ubuntu:
            subprocess.run(["wget", "-q", "-O", f"{dir}/LICENSE", f"https://gitlab.com/tezos/tezos/-/raw/v{version}/LICENSE"], check=True)
        if is_ubuntu:
            subprocess.run(["tar", "-czf", f"{dir}.tar.gz", dir], check=True)
            os.chdir(dir)
            subprocess.run(["dh_make", "-syf" f"../{dir}.tar.gz"], check=True)
            if len(config_files) == 1:
                shutil.copy(f"{os.path.dirname(__file__)}/defaults/{config_files[0]}", f"debian/{package.name.lower()}.default")
            for systemd_unit in package.systemd_units:
                if systemd_unit.service_file.service.environment_file is not None:
                    systemd_unit.service_file.service.environment_file = systemd_unit.service_file.service.environment_file.lower()
                if systemd_unit.suffix is None:
                    print_service_file(systemd_unit.service_file, f"debian/{package.name.lower()}.service")
                else:
                    print_service_file(systemd_unit.service_file, f"debian/{package.name.lower()}-{systemd_unit.suffix}.service")
                shutil.copy(f"{os.path.dirname(__file__)}/scripts/{systemd_unit.startup_script}", f"debian/{systemd_unit.startup_script}")
                gen_install(package, "debian/install")
            gen_control_file(package, "debian/control")
            subprocess.run(["wget", "-q", "-O", "debian/copyright", f"https://gitlab.com/tezos/tezos/-/raw/v{version}/LICENSE"], check=True)
            subprocess.run("rm debian/*.ex debian/*.EX debian/README*", shell=True, check=True)
            gen_changelog(package, "bionic", meta["maintainer"], date, "debian/changelog")
            gen_rules(package, "debian/rules")
            subprocess.run(["dpkg-buildpackage", "-S" if is_source else "-b", "-us", "-uc"],
                           check=True)
            os.chdir("..")
        else:
            for systemd_unit in package.systemd_units:
                if systemd_unit.suffix is None:
                    print_service_file(systemd_unit.service_file, f"{dir}/{package.name}.service")
                else:
                    print_service_file(systemd_unit.service_file, f"{dir}/{package.name}-{systemd_unit.suffix}.service")
                shutil.copy(f"{os.path.dirname(__file__)}/scripts/{systemd_unit.startup_script}", f"{dir}/{systemd_unit.startup_script}")
            if len(config_files) == 1:
                shutil.copy(f"{os.path.dirname(__file__)}/defaults/{config_files[0]}", f"{dir}/{package.name}.default")
            subprocess.run(["tar", "-czf", f"{dir}.tar.gz", dir], check=True)
            os.makedirs(f"{home}/rpmbuild/SPECS", exist_ok=True)
            os.makedirs(f"{home}/rpmbuild/SOURCES", exist_ok=True)
            gen_spec_file(package, f"{home}/rpmbuild/SPECS/{package.name}.spec")
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
            os.rename(f"{artifacts_dir}/{f}", os.path.join("out", f))
