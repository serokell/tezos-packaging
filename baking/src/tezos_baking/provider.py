#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2024 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

import re
import json
import urllib.request

from abc import abstractmethod
from dataclasses import dataclass

from tezos_baking.util import *


def get_node_version():
    version = get_proc_output("octez-node --version").stdout.decode("ascii")
    major_version, minor_version, rc_version = re.search(
        r"[a-z0-9]+ \(.*\) \(([0-9]+).([0-9]+)(?:(?:~rc([1-9]+))|(?:\+dev))?\)",
        version,
    ).groups()
    return (
        int(major_version),
        int(minor_version),
        (int(rc_version) if rc_version is not None else None),
    )


@dataclass
class Provider:
    title: str

    @abstractmethod
    def get_snapshot_metadata(self, network, history_mode, region=None):
        pass


@dataclass
class XtzShotsLike(Provider):
    metadata_url: str
    # Returns relevant snapshot's metadata
    # It filters out provided snapshots by `network` and `history_mode`
    # provided by the user and then follows this steps:
    # * tries to find the snapshot of exact same Octez version, that is used by the user.
    # * if there is none, try to find the snapshot with the same major version, but less minor version
    #   and with the `snapshot_version` compatible with the user's Octez version.
    # * If there is none, try to find the snapshot with any Octez version, but compatible `snapshot_version`.
    def extract_relevant_snapshot(self, snapshot_array, network, history_mode):
        from functools import reduce

        def find_snapshot(pred):
            return next(
                filter(
                    lambda artifact: artifact["artifact_type"] == "tezos-snapshot"
                    and artifact["chain_name"] == network
                    and (
                        artifact["history_mode"] == history_mode
                        or (
                            history_mode == "archive"
                            and artifact["history_mode"] == "full"
                        )
                    )
                    and pred(
                        *(
                            get_artifact_node_version(artifact)
                            + (artifact.get("snapshot_version", None),)
                        )
                    ),
                    iter(snapshot_array),
                ),
                None,
            )

        def get_artifact_node_version(artifact):
            version = artifact["tezos_version"]["version"]
            # there seem to be some inconsistency with that field in different providers
            # so the only thing we check is if it's a string
            additional_info = version["additional_info"]
            return (
                version["major"],
                version["minor"],
                None if type(additional_info) == str else additional_info["rc"],
            )

        def compose_pred(*preds):
            return reduce(
                lambda acc, x: lambda major, minor, rc, snapshot_version: acc(
                    major, minor, rc, snapshot_version
                )
                and x(major, minor, rc, snapshot_version),
                preds,
            )

        def sum_pred(*preds):
            return reduce(
                lambda acc, x: lambda major, minor, rc, snapshot_version: acc(
                    major, minor, rc, snapshot_version
                )
                or x(major, minor, rc, snapshot_version),
                preds,
            )

        node_version = get_node_version()
        major_version, minor_version, rc_version = node_version

        exact_version_pred = (
            lambda major, minor, rc, snapshot_version: node_version
            == (
                major,
                minor,
                rc,
            )
        )

        exact_major_version_pred = (
            lambda major, minor, rc, snapshot_version: major_version == major
        )

        exact_minor_version_pred = (
            lambda major, minor, rc, snapshot_version: minor_version == minor
        )

        less_minor_version_pred = (
            lambda major, minor, rc, snapshot_version: minor_version > minor
        )

        exact_rc_version_pred = (
            lambda major, minor, rc, snapshot_version: rc_version == rc
        )

        less_rc_version_pred = (
            lambda major, minor, rc, snapshot_version: rc
            and rc_version
            and rc_version > rc
        )

        non_rc_version_pred = lambda major, minor, rc, snapshot_version: rc is None

        compatible_version_pred = (
            # it could happen that `snapshot_version` field is not supplied by provider
            # e.g. marigold snapshots don't supply it
            lambda major, minor, rc, snapshot_version: snapshot_version
            and compatible_snapshot_version - snapshot_version <= 2
        )

        non_rc_on_stable_pred = lambda major, minor, rc, snapshot_version: (
            rc_version is None and rc is None
        ) or (rc_version is not None)

        preds = [
            exact_version_pred,
            compose_pred(
                non_rc_on_stable_pred,
                compatible_version_pred,
                sum_pred(
                    compose_pred(
                        exact_major_version_pred,
                        exact_minor_version_pred,
                        less_rc_version_pred,
                    ),
                    compose_pred(
                        exact_major_version_pred,
                        less_minor_version_pred,
                        non_rc_version_pred,
                    ),
                ),
            ),
            compose_pred(
                non_rc_on_stable_pred,
                compatible_version_pred,
            ),
        ]

        return next(
            (
                snapshot
                for snapshot in map(
                    lambda pred: find_snapshot(pred),
                    preds,
                )
                if snapshot is not None
            ),
            None,
        )

    def get_snapshot_metadata(self, network, history_mode, region=None):
        snapshot_array = None
        with urllib.request.urlopen(self.metadata_url) as url:
            snapshot_array = json.load(url)["data"]
        snapshot_array.sort(reverse=True, key=lambda x: x["block_height"])
        return self.extract_relevant_snapshot(snapshot_array, network, history_mode)


class TzInit(Provider):
    def get_filesize(self, url):
        request = urllib.request.Request(
            url, headers=http_request_headers, method="HEAD"
        )
        content_length = next(
            (
                header[1]
                for header in urllib.request.urlopen(request).info()._headers
                if header[0] == "Content-Length"
            ),
            None,
        )
        if content_length is not None:
            suffixes = ["B", "KB", "MB", "GB", "TB", "PB"]
            nbytes = int(content_length)
            i = 0
            while nbytes >= 1024 and i < len(suffixes) - 1:
                nbytes /= 1024.0
                i += 1
            f = ("%.2f" % nbytes).rstrip("0").rstrip(".")
            return "%s%s" % (f, suffixes[i])
        return content_length

    def get_snapshot_metadata(self, network, history_mode, region=None):
        region = "eu" if region is None else region
        history_mode = "full" if history_mode == "archive" else history_mode
        self.metadata_url = (
            f"https://snapshots.{region}.tzinit.org/{network}/{history_mode}.json"
        )
        with urllib.request.urlopen(self.metadata_url) as url:
            snapshot_metadata = json.load(url)["snapshot_header"]

        snapshot_metadata["block_height"] = snapshot_metadata["level"]
        snapshot_metadata[
            "url"
        ] = f"https://snapshots.{region}.tzinit.org/{network}/{history_mode}"
        snapshot_metadata["sha256"] = None
        snapshot_metadata["filesize"] = (
            "not provided"
            if (filesize := self.get_filesize(snapshot_metadata["url"])) is None
            else filesize
        )
        snapshot_metadata["block_timestamp"] = snapshot_metadata["timestamp"]

        return snapshot_metadata


compatible_snapshot_version = 7

default_providers = [
    TzInit("tzinit"),
    XtzShotsLike(
        "marigold.dev", "https://snapshots.tezos.marigold.dev/api/tezos-snapshots.json"
    ),
    XtzShotsLike("xtz-shots.io", "https://xtz-shots.io/tezos-snapshots.json"),
]

recommended_provider = default_providers[0]
