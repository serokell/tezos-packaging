# SPDX-FileCopyrightText: 2023 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

"""
Write doc.
"""

import sys, subprocess, shlex
import re
import urllib.request
import json

# Regexes

secret_key_regex = b"(encrypted|unencrypted):(?:\w{54}|\w{88})"
address_regex = b"tz[123]\w{33}"
protocol_hash_regex = (
    b"P[123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz]{50}"
)
signer_uri_regex = b"((?:tcp|unix|https|http):\/\/.+)\/(tz[123]\w{33})\/?"
ledger_regex = b"ledger:\/\/[\w\-]+\/[\w\-]+\/[\w']+\/[\w']+"
derivation_path_regex = b"(?:bip25519|ed25519|secp256k1|P-256)\/[0-9]+h\/[0-9]+h"


# Utilities


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
                f"sudo sed -i 's/{old.group(0)}/{new}/' {env_file.decode('utf8')}"
            )


def progressbar_hook(chunk_number, chunk_size, total_size):
    done = chunk_number * chunk_size
    percent = min(int(done * 100 / total_size), 100)
    print("Progress:", percent, "%,", int(done / (1024 * 1024)), "MB", end="\r")


def color(input, colorcode):
    return colorcode + input + "\x1b[0m"


color_red = "\x1b[1;31m"


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


http_request_headers = {"User-Agent": "Mozilla/5.0"}


# Wizard CLI skeleton


suppress_warning_text = "TEZOS_CLIENT_UNSAFE_DISABLE_DISCLAIMER=YES"


def get_data_dir(network):
    node_env = get_systemd_service_env(f"tezos-node-{network}")
    data_dir = node_env.get("TEZOS_NODE_DIR")
    if data_dir is None:
        print(
            "TEZOS_NODE_DIR is undefined, defaulting to /var/lib/tezos/node-" + network
        )
        return "/var/lib/tezos/node-" + network
    return data_dir


def get_key_address(tezos_client_options, key_alias):
    address = get_proc_output(
        f"sudo -u tezos {suppress_warning_text} octez-client {tezos_client_options} "
        f"show address {key_alias} --show-secret"
    )
    if address.returncode == 0:
        value_regex = (
            b"(?:"
            + ledger_regex
            + b")|(?:"
            + secret_key_regex
            + b")|(?:remote\:"
            + address_regex
            + b")"
        )
        value = re.search(value_regex, address.stdout).group(0).decode()
        address = re.search(address_regex, address.stdout).group(0).decode()
        return (value, address)
    else:
        return None


def wait_for_ledger_app(ledger_app, client_dir):
    output = b""
    try:
        while re.search(f"Found a Tezos {ledger_app}".encode(), output) is None:
            output = get_proc_output(
                f"sudo -u tezos {suppress_warning_text} octez-client --base-dir {client_dir} list connected ledgers"
            ).stdout
            proc_call("sleep 1")
    except KeyboardInterrupt:
        return None
    ledgers_derivations = {}
    for ledger_derivation in re.findall(ledger_regex, output):
        ledger_url = (
            re.search(b"ledger:\/\/[\w\-]+\/", ledger_derivation).group(0).decode()
        )
        derivation_path = (
            re.search(derivation_path_regex, ledger_derivation).group(0).decode()
        )
        ledgers_derivations.setdefault(ledger_url, []).append(derivation_path)
    return ledgers_derivations


def ledger_urls_info(ledgers_derivations, node_endpoint, client_dir):
    ledgers_info = {}
    max_derivation_len = 0
    for derivations_paths in ledgers_derivations.values():
        max_derivation_len = max(max_derivation_len, max(map(len, derivations_paths)))
    for ledger_url, derivations_paths in ledgers_derivations.items():
        for derivation_path in derivations_paths:
            output = get_proc_output(
                f"sudo -u tezos {suppress_warning_text} octez-client --base-dir {client_dir} "
                f"show ledger {ledger_url + derivation_path}"
            ).stdout
            addr = re.search(address_regex, output).group(0).decode()
            balance = (
                get_proc_output(
                    f"sudo -u tezos {suppress_warning_text} octez-client --base-dir {client_dir} "
                    f"--endpoint {node_endpoint} get balance for {addr}"
                )
                .stdout.decode()
                .strip()
            )
            ledgers_info.setdefault(ledger_url, []).append(
                (
                    "{:" + str(max_derivation_len + 1) + "} address: {}, balance: {}"
                ).format(derivation_path + ",", addr, balance)
            )
    return ledgers_info


def search_json_with_default(json_filepath, field, default):
    with open(json_filepath, "r") as f:
        try:
            json_dict = json.load(f)
        except:
            return default
        return json_dict.pop(field, default)
