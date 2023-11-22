# SPDX-FileCopyrightText: 2021 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ

import os, json


class PackagesMeta:
    def __init__(
        self, version, release, ubuntu_epoch, fedora_epoch, maintainer, license_version
    ):
        self.version = version
        self.release = release
        self.ubuntu_epoch = ubuntu_epoch
        self.fedora_epoch = fedora_epoch
        self.maintainer = maintainer
        self.license_version = license_version

version = ""
with open("meta.json", "r") as f:
    version = json.load(f)["tezos_ref"]
version = os.environ.get("OCTEZ_VERSION", version)[1:]

meta_json_contents = json.load(
    open(f"{os.path.dirname(__file__)}/../../meta.json", "r")
)
packages_meta = PackagesMeta(
    version=version,
    release=str(meta_json_contents["release"]),
    ubuntu_epoch=2,
    fedora_epoch=1,
    maintainer=meta_json_contents["maintainer"],
    license_version=os.getenv("TEZOS_LICENSE_VERSION", f"v{version}"),
)
