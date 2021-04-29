# SPDX-FileCopyrightText: 2021 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ

import os, json


class PackagesMeta:
    def __init__(self, version, release, ubuntu_epoch, fedora_epoch, maintainer):
        self.version = version
        self.release = release
        self.ubuntu_epoch = ubuntu_epoch
        self.fedora_epoch = fedora_epoch
        self.maintainer = maintainer


meta_json_contents = json.load(
    open(f"{os.path.dirname(__file__)}/../../meta.json", "r")
)
packages_meta = PackagesMeta(
    version=os.environ["TEZOS_VERSION"][1:],
    release=str(meta_json_contents["release"]),
    ubuntu_epoch=2,
    fedora_epoch=1,
    maintainer=meta_json_contents["maintainer"],
)
