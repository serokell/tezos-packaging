# SPDX-FileCopyrightText: 2023 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

"""
Common utilities
"""

import sys, subprocess, shlex
import re
import urllib.request
import os
import logging

# Regexes and constants

__all__ = ["TMP_SNAPSHOT_LOCATION"]

secret_key_regex = b"(encrypted|unencrypted):(?:\w{54}|\w{88})"
address_regex = b"tz[123]\w{33}"
protocol_hash_regex = (
    b"P[123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz]{50}"
)
signer_uri_regex = b"((?:tcp|unix|https|http):\/\/.+)\/(tz[123]\w{33})\/?"
ledger_regex = b"ledger:\/\/[\w\-]+\/[\w\-]+\/[\w']+\/[\w']+"
derivation_path_regex = b"(?:bip25519|ed25519|secp256k1|P-256)\/[0-9]+h\/[0-9]+h"

compatible_snapshot_version = 7
TMP_SNAPSHOT_LOCATION = "/tmp/octez_node.snapshot.d/"


# Utilities

http_request_headers = {"User-Agent": "Mozilla/5.0"}

suppress_warning_text = "TEZOS_CLIENT_UNSAFE_DISABLE_DISCLAIMER=YES"


def proc_call(cmd):
    return subprocess.check_call(shlex.split(cmd))


def get_proc_output(cmd):
    if sys.version_info.major == 3 and sys.version_info.minor < 7:
        return subprocess.run(shlex.split(cmd), stdout=subprocess.PIPE)
    else:
        return subprocess.run(shlex.split(cmd), capture_output=True)


def show_systemd_service(service_name):
    return get_proc_output(f"systemctl show {service_name}.service").stdout


def find_systemd_env_files(show_systemd_output):
    return re.findall(b"EnvironmentFiles?=(.*) ", show_systemd_output)


def find_systemd_unit_env(show_systemd_output):
    unit_env = re.search(b"Environment=(.*)(?:$|\n)", show_systemd_output)
    if unit_env is not None:
        return unit_env.group(1).decode("utf-8")
    return ""


def print_and_log(message, log=logging.info, colorcode=None):
    print(color(message, colorcode) if colorcode else message)
    log(message)


# Returns all the environment variables of a systemd service unit
# Note: definitions directly in the unit (not in environment files) take precedence
def get_systemd_service_env(service_name):
    result = dict()
    sys_show = show_systemd_service(service_name)

    for env_file in find_systemd_env_files(sys_show):
        with open(env_file, "r") as f:
            for line in f:
                env_def = re.search("^(\w+)=(.*)\n", line)
                if env_def is not None:
                    env_var = env_def.group(1)
                    var_val = env_def.group(2).strip('"')
                    result[env_var] = var_val

    env_matches = re.findall(
        r'(\w+)=(("(?:\\.|[^"\\])*")|([\S]+))',
        find_systemd_unit_env(sys_show),
    )
    for env_match in env_matches:
        env_var = env_match[0]
        var_val = env_match[1].strip('"')
        result[env_var] = var_val

    return result


def replace_systemd_service_env(service_name, field, value):
    for env_file in find_systemd_env_files(show_systemd_service(service_name)):
        with open(env_file, "r") as f:
            config_contents = f.read()

        old = re.search(f"{field}=.*", config_contents)
        if old is not None:
            new = f"{field}={value}"
            proc_call(
                f"sudo sed -i 's|{old.group(0)}|{new}|' {env_file.decode('utf8')}"
            )


def progressbar_hook(chunk_number, chunk_size, total_size):
    done = chunk_number * chunk_size
    percent = min(int(done * 100 / total_size), 100)
    print("Progress:", percent, "%,", int(done / (1024 * 1024)), "MB", end="\r")


def color(input, colorcode):
    return colorcode + input + "\x1b[0m"


color_red = "\x1b[1;31m"
color_green = "\x1b[1;32m"
color_yellow = "\x1b[1;33m"


def yes_or_no(prompt, default=None):
    valid = False
    while not valid:
        answer = input(prompt).strip().lower()
        if not answer and default is not None:
            answer = default
        if answer in ["y", "yes"]:
            print()
            return True
        elif answer in ["n", "no"]:
            print()
            return False
        else:
            print(color("Please provide a 'yes' or 'no' answer.", color_red))


def mk_full_url(host_name, path):
    from urllib.parse import urlparse

    url = host_name
    if path is not None:
        url = os.path.join(host_name, path)

    # urllib doesn't make an assumption which scheme to use by default in case of absence
    if urlparse(url).scheme == "":
        url = "https://" + url

    return url


def url_is_reachable(url):
    req = urllib.request.Request(url, headers=http_request_headers)
    try:
        urllib.request.urlopen(req)
        return True
    except (urllib.error.URLError, ValueError):
        return False


def fetch_snapshot(url, sha256=None):

    logging.info("Fetching snapshot")

    dirname = TMP_SNAPSHOT_LOCATION
    filename = os.path.join(dirname, "octez_node.snapshot")
    metadata_file = os.path.join(dirname, "octez_node.snapshot.sha256")

    # updates or removes the 'metadata_file' containing the snapshot's SHA256
    def dump_metadata(metadata_file=metadata_file, sha256=sha256):
        if sha256:
            with open(metadata_file, "w+") as f:
                f.write(sha256)
        else:
            try:
                os.remove(metadata_file)
            except FileNotFoundError:
                pass

    # reads `metadata_file` if any or returns None
    def read_metadata(metadata_file=metadata_file):
        if os.path.exists(metadata_file):
            with open(metadata_file, "r") as f:
                sha256 = f.read()
            return sha256
        else:
            return None

    def download(filename=filename, url=url, args=""):
        from subprocess import CalledProcessError

        try:
            proc_call(f"wget {args} --show-progress -O {filename} {url}")
        except CalledProcessError as e:
            # see here https://www.gnu.org/software/wget/manual/html_node/Exit-Status.html
            if e.returncode >= 4:
                raise urllib.error.URLError
            else:
                raise e

    print_and_log(f"Downloading the snapshot from {url}")

    # expected for the (possibly) existing chunk
    expected_sha256 = read_metadata()

    os.makedirs(dirname, exist_ok=True)
    if sha256 and expected_sha256 and expected_sha256 == sha256:
        logging.info("Continuing download")
        # that case means that the expected sha256 of snapshot
        # we want to download is the same as the expected
        # sha256 of the existing octez_node.snapshot file
        # when it will be fully downloaded
        # so that we can safely use `--continue` option here
        download(args="--continue")
    else:
        # all other cases we just dump new metadata
        # (so that we can resume download if we can ensure
        # that existing octez_node.snapshot chunk belongs
        # to the snapshot we want to download)
        # and start download from scratch
        dump_metadata()
        download()

    print()
    return filename


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


# Returns relevant snapshot's metadata
# It filters out provided snapshots by `network` and `history_mode`
# provided by the user and then follows this steps:
# * tries to find the snapshot of exact same Octez version, that is used by the user.
# * if there is none, try to find the snapshot with the same major version, but less minor version
#   and with the `snapshot_version` compatible with the user's Octez version.
# * If there is none, try to find the snapshot with any Octez version, but compatible `snapshot_version`.
def extract_relevant_snapshot(snapshot_array, config):
    from functools import reduce

    def find_snapshot(pred):
        return next(
            filter(
                lambda artifact: artifact["artifact_type"] == "tezos-snapshot"
                and artifact["chain_name"] == config["network"]
                and (
                    artifact["history_mode"] == config["history_mode"]
                    or (
                        config["history_mode"] == "archive"
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

    exact_version_pred = lambda major, minor, rc, snapshot_version: node_version == (
        major,
        minor,
        rc,
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

    exact_rc_version_pred = lambda major, minor, rc, snapshot_version: rc_version == rc

    less_rc_version_pred = (
        lambda major, minor, rc, snapshot_version: rc and rc_version and rc_version > rc
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
