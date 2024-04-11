# SPDX-FileCopyrightText: 2021 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ

import os, json


class PackagesMeta:
    def __init__(
        self,
        tag,
        version,
        release,
        ubuntu_epoch,
        fedora_epoch,
        maintainer,
        license_version,
    ):
        self.tag = tag
        self.version = version
        self.release = release
        self.ubuntu_epoch = ubuntu_epoch
        self.fedora_epoch = fedora_epoch
        self.maintainer = maintainer
        self.license_version = license_version


tag = os.environ["OCTEZ_VERSION"]
for (i, c) in enumerate(tag):
    if c.isdigit():
        digit_index = i
        break
version = tag[digit_index:]

meta_json_contents = json.load(
    open(f"{os.path.dirname(__file__)}/../../meta.json", "r")
)
packages_meta = PackagesMeta(
    tag=tag,
    version=version,
    release=str(meta_json_contents["release"]),
    ubuntu_epoch=2,
    fedora_epoch=1,
    maintainer=meta_json_contents["maintainer"],
    license_version=os.getenv("TEZOS_LICENSE_VERSION", tag),
)
