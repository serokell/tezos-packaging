#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2020 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: MPL-2.0

import os, sys, subprocess, json
from distutils.dir_util import copy_tree

class Package:
    def __init__(self, name, desc, systemd_unit=None):
        self.name = name
        self.desc = desc
        self.systemd_unit = systemd_unit

class SystemdUnit:
    def __init__(self, name, startup_script, config_file):
        self.name = name
        self.startup_script = startup_script
        self.config_file = config_file

if sys.argv[1] == "source":
    is_source = True
elif sys.argv[1] == "binary":
    is_source = False
else:
    raise Exception("Unexpected package format, only 'source' and 'binary' are supported.")

package_to_build = None
if len(sys.argv) == 3:
    package_to_build = sys.argv[2]

date = subprocess.check_output(["date", "-R"]).decode().strip()
meta = json.load(open("../meta.json", "r"))
tezos_sources = json.load(open("../nix/nix/sources.json", "r"))["tezos"]

common_deps = ["libev-dev", "libgmp-dev", "libhidapi-dev", "m4", "perl", "pkg-config",
               "wget", "unzip", "rsync"]

active_protocols = json.load(open("../protocols.json", "r"))["active"]

version = f"{tezos_sources['ref'][1:]}"
release = f"{meta['release']}"
package_version = f"{meta['epoch']}:0ubuntu{version}-{release}"


def gen_control_file(pkg: Package, out):
    str_deps = ", ".join(common_deps)
    file_contents = f'''
Source: {pkg.name.lower()}
Section: utils
Priority: optional
Maintainer: {meta['maintainer']}
Build-Depends: debhelper (>=9), dh-systemd (>= 1.5), autotools-dev, {str_deps}
Standards-Version: 3.9.6
Homepage: https://gitlab.com/tezos/tezos/

Package: {pkg.name.lower()}
Architecture: amd64
Depends: ${{shlibs:Depends}}, ${{misc:Depends}}
Description: {pkg.desc}
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
    changelog_contents = f'''{pkg.name.lower()} ({package_version}) {ubuntu_version}; urgency=medium

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
            "CLI client for interacting with tezos blockchain"),
    Package("tezos-admin-client",
            "Administration tool for the node") ,
    Package("tezos-node",
            "Entry point for initializing, configuring and running a Tezos node",
            SystemdUnit("tezos-node.service", "tezos-node-start", "tezos-node.conf")
    ),
    Package("tezos-signer",
            "A client to remotely sign operations or blocks")
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
            Package(f"tezos-{daemon}-{protocol}",
                    daemon_decs[daemon],
                    SystemdUnit(f"tezos-{daemon}.service", f"tezos-{daemon}-start", f"tezos-{daemon}.conf")
            )
        )

for package in packages:
    if package_to_build is None or package.name == package_to_build:
        dir = f"{package.name.lower()}-0ubuntu{version}"
        # tezos-client and tezos-admin-client are in one opam package
        opam_package = "tezos-client" if package.name == "tezos-admin-client" else package.name
        subprocess.run(["opam", "exec", "--", "opam-bundle", f"{opam_package}={version}",
                        "--ocaml=4.09.1", "--yes", "--opam=2.0.5"], check=True)
        subprocess.run(["tar", "-zxf", f"{opam_package}-bundle.tar.gz"], check=True)
        os.rename(f"{opam_package}-bundle", dir)
        gen_makefile(package, f"{dir}/Makefile")
        subprocess.run(["tar", "-czf", f"{dir}.tar.gz", dir], check=True)
        os.chdir(dir)
        subprocess.run(["dh_make", "-syf" f"../{dir}.tar.gz"], check=True)
        if package.systemd_unit is not None:
            os.rename(f"../systemd/{package.systemd_unit.name}", f"debian/{package.name.lower()}.service")
            os.rename(f"../defaults/{package.systemd_unit.config_file}", f"debian/{package.name.lower()}.default")
            os.rename(f"../scripts/{package.systemd_unit.startup_script}", f"debian/{package.systemd_unit.startup_script}")
            gen_install(package, "debian/install")
        gen_control_file(package, "debian/control")
        subprocess.run(["wget", "-q", "-O", "debian/copyright", f"https://gitlab.com/tezos/tezos/-/raw/v{version}/LICENSE"], check=True)
        subprocess.run("rm debian/*.ex debian/*.EX debian/README*", shell=True, check=True)
        gen_changelog(package, "bionic", meta["maintainer"], date, "debian/changelog")
        gen_rules("debian/rules")
        subprocess.run(["dpkg-buildpackage", "-S" if is_source else "-b", "-us", "-uc"],
                       check=True)
        os.chdir("..")
        subprocess.run(f"rm -rf {dir}", shell=True, check=True)

os.mkdir("out")
if not is_source:
    exts = [".deb"]
else:
    exts = [".orig.tar.gz", ".dsc", ".changes", ".debian.tar.xz", ".buildinfo"]
for f in os.listdir("."):
    for ext in exts:
        if f.endswith(ext):
            os.rename(f, os.path.join("out", f))
