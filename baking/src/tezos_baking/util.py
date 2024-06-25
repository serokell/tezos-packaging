# SPDX-FileCopyrightText: 2023 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

"""
Common utilities
"""

import sys, subprocess, shlex
import re
import urllib.request
import json
import os

# Regexes

secret_key_regex = b"(encrypted|unencrypted):(?:\\w{54}|\\w{88})"
address_regex = b"tz[123]\\w{33}"
protocol_hash_regex = (
    b"P[123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz]{50}"
)
signer_uri_regex = b"((?:tcp|unix|https|http):\\/\\/.+)\\/(tz[123]\\w{33})\\/?"
ledger_regex = b"ledger:\\/\\/[\\w\\-]+\\/[\\w\\-]+\\/[\\w']+\\/[\\w']+"
derivation_path_regex = b"(?:bip25519|ed25519|secp256k1|P-256)\\/[0-9]+h\\/[0-9]+h"


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


# Returns all the environment variables of a systemd service unit
# Note: definitions directly in the unit (not in environment files) take precedence
def get_systemd_service_env(service_name):
    result = dict()
    sys_show = show_systemd_service(service_name)

    for env_file in find_systemd_env_files(sys_show):
        with open(env_file, "r") as f:
            for line in f:
                env_def = re.search("^(\\w+)=(.*)\n", line)
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
