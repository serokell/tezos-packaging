#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2021 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ

"""
A wizard utility to help set up tezos-baker.

Asks questions, validates answers, and executes the appropriate steps using the final configuration.
"""

import os, sys, subprocess, shlex, shutil
import readline
import re, textwrap
import urllib.request
import json
from typing import List


# Global options

networks = {
    "mainnet": "Main Tezos network",
    "hangzhounet": "Test network using version 011 of Tezos protocol (Hangzhou)",
    "ithacanet": "Test network using version 012 of Tezos protocol (Ithaca2)",
}

modes = {
    "baking": "Set up and start all services for baking: "
    "tezos-node, tezos-baker, and tezos-endorser.",
    "node": "Only bootstrap and run the Tezos node.",
}

snapshot_import_modes = {
    "download rolling": "Import rolling snapshot from xtz-shots.io (recommended)",
    "download full": "Import full snapshot from xtz-shots.io",
    "file": "Import snapshot from a file",
    "url": "Import snapshot from a url",
    "skip": "Skip snapshot import and synchronize with the network from scratch",
}

key_import_modes = {
    "ledger": "From a ledger",
    "secret-key": "Either the unencrypted or password-encrypted secret key for your address",
    "json": "Faucet JSON file from https://faucet.tzalpha.net/",
}

systemd_enable = {
    "yes": "Enable the services, running them both now and on every boot",
    "no": "Start the services this time only",
}

history_modes = {
    "rolling": "Store a minimal rolling window of chain data, lightest option",
    "full": "Store enough chain data to reconstruct the complete chain state",
    "archive": "Store all the chain data, very storage-demanding",
}


TMP_SNAPSHOT_LOCATION = "/tmp/tezos_node.snapshot"

# Regexes

ledger_regex = b"ledger:\/\/[\w\-]+\/[\w\-]+\/[\w']+\/[\w']+"
secret_key_regex = b"(encrypted|unencrypted):(?:\w{54}|\w{88})"
address_regex = b"tz[123]\w{33}"
derivation_path_regex = b"(?:bip25519|ed25519|secp256k1|P-256)\/[0-9]+h\/[0-9]+h"

# Input validators


def enum_range_validator(options):
    def _validator(input):
        intrange = list(map(str, range(1, len(options) + 1)))
        if input not in intrange and input not in options:
            raise ValueError(
                "Please choose one of the provided values or use their respective numbers: "
                + ", ".join(options)
            )
        try:
            opt = int(input) - 1
        except:
            return input
        else:
            opts = options
            if isinstance(options, dict):
                opts = list(options.keys())
            return opts[opt]

    return _validator


def filepath_validator(input):
    if input and not os.path.isfile(input):
        raise ValueError("Please input a valid file path.")
    return input


def required_field_validator(input):
    if not input.strip():
        raise ValueError("Please provide this required option.")
    return input


# The input has to be valid to at least one of the two passed validators.
def or_validator(validator1, validator2):
    def _validator(input):
        try:
            return validator1(input)
        except:
            return validator2(input)

    return _validator


# Runs the input through the passed validator, allowing for possible alteration,
# but doesn't raise an exception if it doesn't validate to allow for custom options, too.
def or_custom_validator(validator):
    def _validator(input):
        result = input
        try:
            result = validator(input)
        except:
            pass
        return result

    return _validator


# To be validated, the input should adhere to the Tezos secret key format:
# {encrypted, unencrypted}:<base58 encoded string with length 54 or 88>
def secret_key_validator(input):
    match = re.match(secret_key_regex.decode("utf-8"), input.strip())
    if not bool(match):
        raise ValueError(
            "The input doesn't match the format for the Tezos secret key: "
            "{{encrypted, unencrypted}:<base58 encoded string with length 54 or 88>}"
            "\nPlease check the input and try again."
        )
    return input


# To be validated, the input should adhere to the derivation path format:
# [0-9]+h/[0-9]+h
def derivation_path_validator(input):
    match = re.match(b"[0-9]+h\/[0-9]+h".decode("utf-8"), input.strip())
    if not bool(match):
        raise ValueError(
            "The input doesn't match the format for the derivation path: "
            "'[0-9]+h/[0-9]+h'"
            "\nPlease check the input and try again."
        )
    return input


class Validator:
    def __init__(self, validator):
        self.validator = validator

    def validate(self, input):
        if self.validator is not None:
            if isinstance(self.validator, list):
                for v in self.validator:
                    input = v(input)
                return input
            else:
                return self.validator(input)


# Wizard CLI utility


suppress_warning_text = "TEZOS_CLIENT_UNSAFE_DISABLE_DISCLAIMER=YES"


def proc_call(cmd):
    return subprocess.check_call(shlex.split(cmd))


def get_proc_output(cmd):
    if sys.version_info.major == 3 and sys.version_info.minor < 7:
        return subprocess.run(shlex.split(cmd), stdout=subprocess.PIPE)
    else:
        return subprocess.run(shlex.split(cmd), capture_output=True)


def fetch_snapshot(url):
    print("Downloading the snapshot from", url)
    filename = TMP_SNAPSHOT_LOCATION
    urllib.request.urlretrieve(url, filename, progressbar_hook)
    print()
    return filename


def progressbar_hook(chunk_number, chunk_size, total_size):
    done = chunk_number * chunk_size
    percent = min(int(done * 100 / total_size), 100)
    print("Progress:", percent, "%,", int(done / (1024 * 1024)), "MB", end="\r")


def color(input, colorcode):
    return colorcode + input + "\x1b[0m"


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
            print(color("Please provide a 'yes' or 'no' answer.", "\x1b[1;31m"))


def wait_for_ledger_baking_app():
    output = b""
    while re.search(b"Found a Tezos Baking", output) is None:
        output = get_proc_output(
            f"sudo -u tezos {suppress_warning_text} tezos-client list connected ledgers"
        ).stdout
        proc_call("sleep 1")
    base_ledger_url = (
        re.search(b"ledger:\/\/[\w\-]+\/", output).group(0).decode("utf-8")
    )
    return base_ledger_url, [
        name.decode() for name in re.findall(derivation_path_regex, output)
    ]


def get_data_dir(network):
    output = get_proc_output("systemctl show tezos-node-" + network + ".service").stdout
    config = re.search(b"Environment=(.*)(?:$|\n)", output)
    if config is None:
        print(
            "tezos-node-" + network + ".service configuration not found, "
            "defaulting to /var/lib/tezos/node-" + network
        )
        return "/var/lib/tezos/node-" + network
    config = config.group(1)
    data_dir = re.search(b"DATA_DIR=(.*?)(?: |$|\n)", config)
    if data_dir is not None:
        return data_dir.group(1).decode("utf-8")
    else:
        print("DATA_DIR is undefined, defaulting to /var/lib/tezos/node-" + network)
        return "/var/lib/tezos/node-" + network


def ledger_urls_info(ledger_derivations, base_ledger_url, node_endpoint):
    info = []
    # max accepts only non-empty lists
    if len(ledger_derivations) == 0:
        return info
    max_derivation_len = max(map(len, ledger_derivations))
    for derivation in ledger_derivations:
        output = get_proc_output(
            f"sudo -u tezos {suppress_warning_text} tezos-client "
            f"show ledger {base_ledger_url + derivation}"
        ).stdout
        addr = re.search(address_regex, output).group(0).decode()
        balance = (
            get_proc_output(
                f"sudo -u tezos {suppress_warning_text} tezos-client "
                f"--endpoint {node_endpoint} get balance for {addr}"
            )
            .stdout.decode()
            .strip()
        )
        info.append(
            ("{:" + str(max_derivation_len + 1) + "} address: {}, balance: {}").format(
                derivation + ",", addr, balance
            )
        )
    return info


def search_baking_service_config(config_contents, regex, default):
    res = re.search(regex, config_contents)
    if res is None:
        return default
    else:
        return res.group(1)


def is_full_snapshot(import_mode):
    if import_mode == "download full":
        return True
    if import_mode == "file" or import_mode == "url":
        output = get_proc_output(
            "sudo -u tezos tezos-node snapshot info " + TMP_SNAPSHOT_LOCATION
        ).stdout
        return re.search(b"at level [0-9]+ in full", output) is not None
    return False


class Step:
    def __init__(
        self,
        id: str,
        prompt: str,
        help: str,
        default: str = "1",
        options=None,
        validator=None,
    ):
        self.id = id
        self.prompt = prompt
        self.help = help
        self.default = default
        self.options = options
        self.validator = validator

    def pprint_options(self):
        i = 1
        def_i = None
        try:
            def_i = int(self.default)
        except:
            pass

        if self.options and isinstance(self.options, list):
            str_format = "{:1}. {}"
            for o in self.options:
                if def_i is not None and i == def_i:
                    print(str_format.format(i, "(default) " + o))
                else:
                    print(str_format.format(i, o))
                i += 1
        elif self.options and isinstance(self.options, dict):
            str_format = "{:1}. {:<26}  {}"
            for o in self.options:
                description = textwrap.indent(
                    textwrap.fill(self.options[o], 60), " " * 31
                ).lstrip()
                if def_i is not None and i == def_i:
                    print(str_format.format(i, o + " (default)", description))
                else:
                    print(str_format.format(i, o, description))
                i += 1


# Steps

network_query = Step(
    id="network",
    prompt="Which Tezos network would you like to use?\nCurrently supported:",
    help="The selected network will be used to set up all required services.\n"
    "The currently supported protocol is 011-PtHangz2 (used on hangzhounet and mainnet).\n"
    "\nKeep in mind that you must select the test network "
    "(hangzhounet) if you plan on baking with a faucet JSON file.",
    options=networks,
    validator=Validator(enum_range_validator(networks)),
)

service_mode_query = Step(
    id="mode",
    prompt="Do you want to set up baking or to run the standalone node?",
    help="By default, tezos-baking provides predefined services for running baking instances "
    "on different networks.\nSometimes, however, you might want to only run the Tezos node.\n"
    "When this option is chosen, this wizard will help you bootstrap tezos-node only.",
    options=modes,
    validator=Validator(enum_range_validator(modes)),
)

systemd_mode_query = Step(
    id="systemd_mode",
    prompt="Would you like your setup to automatically start on boot?",
    help="Starting the service will make it available just for this session, great\n"
    "if you want to experiment. Enabling it will make it start on every boot.",
    options=systemd_enable,
    validator=Validator(enum_range_validator(systemd_enable)),
)

# We define this step as a function to better tailor snapshot options to the chosen history mode
def get_snapshot_mode_query(modes):
    return Step(
        id="snapshot",
        prompt="The Tezos node can take a significant time to bootstrap from scratch.\n"
        "Bootstrapping from a snapshot is suggested instead.\n"
        "How would you like to proceed?",
        help="A fully-synced local tezos-node is required for running a baking instance.\n"
        "By default, service with tezos-node will start to bootstrap from scratch,\n"
        "which will take a significant amount of time.\nIn order to avoid this, we suggest "
        "bootstrapping from a snapshot instead.\n\n"
        "Snapshots can be downloaded from the following websites:\n"
        "Tezos Giganode Snapshots - https://snapshots-tezos.giganode.io/ \n"
        "XTZ-Shots - https://xtz-shots.io/ \n\n"
        "We recommend to use rolling snapshots. This is the smallest and the fastest mode\n"
        "that is sufficient for baking. You can read more about other tezos-node history modes here:\n"
        "https://tezos.gitlab.io/user/history_modes.html#history-modes",
        options=modes,
        validator=Validator(enum_range_validator(modes)),
    )


snapshot_file_query = Step(
    id="snapshot_file",
    prompt="Provide the path to the tezos-node snapshot file.",
    help="You have indicated wanting to import the snapshot from a file.\n"
    "You can download the snapshot yourself e.g. from XTZ-Shots or Tezos Giganode Snapshots.",
    validator=Validator(filepath_validator),
)

snapshot_url_query = Step(
    id="snapshot_url",
    prompt="Provide the url of the tezos-node snapshot file.",
    help="You have indicated wanting to import the snapshot from a custom url.\n"
    "You can use e.g. links to XTZ-Shots or Tezos Giganode Snapshots resources.",
)

history_mode_query = Step(
    id="history_mode",
    prompt="Which history mode do you want your node to run in?",
    help="History modes govern how much data tezos-node stores, and, consequently, how much disk\n"
    "space is required. Rolling mode is the smallest and fastest but still sufficient for baking.\n"
    "You can read more about different tezos-node history modes here:\n"
    "https://tezos.gitlab.io/user/history_modes.html",
    options=history_modes,
    validator=Validator(enum_range_validator(history_modes)),
)

# We define the step as a function to disallow choosing json baking on mainnet
def get_key_mode_query(modes):
    return Step(
        id="key_import_mode",
        prompt="How do you want to import the baker key?",
        help="To register the baker, its secret key needs to be imported to the data "
        "directory first.\nBy default tezos-baking-<network>.service will use the 'baker' "
        "alias\nfor the key that will be used for baking and endorsing.\n"
        "If you want to test baking with a faucet file, "
        "make sure you have chosen a test network like " + list(networks.keys())[1],
        options=modes,
        validator=Validator(enum_range_validator(modes)),
    )


secret_key_query = Step(
    id="secret_key",
    prompt="Provide either the unencrypted or password-encrypted secret key for your address.",
    help="The format is 'unencrypted:edsk...' for the unencrypted key, or 'encrypted:edesk...'"
    "for the encrypted key.",
    validator=Validator([required_field_validator, secret_key_validator]),
)

json_filepath_query = Step(
    id="json_filepath",
    prompt="Provide the path to your downloaded faucet JSON file.",
    help="Download the faucet JSON file from https://faucet.tzalpha.net/.\n"
    "The file will contain the 'mnemonic' and 'secret' fields.",
    validator=Validator([required_field_validator, filepath_validator]),
)

derivation_path_query = Step(
    id="derivation_path",
    prompt="Provide derivation path for the key stored on the ledger.",
    help="The format is '[0-9]+h/[0-9]+h'",
    validator=Validator([required_field_validator, derivation_path_validator]),
)

# We define this step as a function since the corresponding step requires
# tezos-node to be running and bootstrapped in order to gather the data
# about the ledger-stored addresses, so it's called right before invoking
# after the node was boostrapped
def get_ledger_derivation(ledger_derivations, base_ledger_url, node_endpoint):
    extra_options = ["Specify derivation path", "Go back"]
    return Step(
        id="ledger_derivation",
        prompt="Select a key to import from " + base_ledger_url + ".\n"
        "You can choose one of the suggested derivations or provide your own:",
        help="'Specify derivation path' will ask a derivation path from you."
        "'Go back' will return you back to the key type choice.",
        default=None,
        options=ledger_urls_info(ledger_derivations, base_ledger_url, node_endpoint)
        + extra_options,
        validator=Validator(
            [
                required_field_validator,
                enum_range_validator(ledger_derivations + extra_options),
            ]
        ),
    )


class Setup:
    def __init__(self, config={}):
        self.config = config

    def query_step(self, step: Step):

        validated = False
        while not validated:
            print(step.prompt)
            step.pprint_options()
            answer = input("> ").strip()

            if answer.lower() in ["quit", "exit"]:
                raise KeyboardInterrupt
            elif answer.lower() in ["help", "?"]:
                print(step.help)
                print()
            else:
                if not answer and step.default is not None:
                    answer = step.default

                try:
                    if step.validator is not None:
                        answer = step.validator.validate(answer)
                except ValueError as e:
                    print(color("Validation error: " + str(e), "\x1b[1;31m"))
                else:
                    validated = True
                    self.config[step.id] = answer

    def fill_baking_config(self):
        network = self.config["network"]
        output = get_proc_output(
            "systemctl show tezos-baking-" + network + ".service"
        ).stdout
        config_filepath = re.search(b"EnvironmentFiles=(.*) ", output)
        if config_filepath is None:
            print(
                "EnvironmentFiles not found in tezos-baking-"
                + network
                + ".service configuration,",
                "defaulting to /etc/default/tezos-baking-" + network,
            )
            config_filepath = "/etc/default/tezos-baking-" + network
        else:
            config_filepath = config_filepath.group(1).decode().strip()

        with open(config_filepath, "r") as f:
            config_contents = f.read()
            self.config["client_data_dir"] = search_baking_service_config(
                config_contents, 'DATA_DIR="(.*)"', "/var/lib/.tezos-client"
            )
            self.config["node_rpc_addr"] = search_baking_service_config(
                config_contents, 'NODE_RPC_ENDPOINT="(.*)"', "http://localhost:8732"
            )
            self.config["baker_alias"] = search_baking_service_config(
                config_contents, 'BAKER_ADDRESS_ALIAS="(.*)"', "baker"
            )

    def get_tezos_client_options(self):
        return (
            "--base-dir "
            + self.config["client_data_dir"]
            + " --endpoint "
            + self.config["node_rpc_addr"]
        )

    def get_current_head_level(self):
        response = urllib.request.urlopen(
            self.config["node_rpc_addr"] + "/chains/main/blocks/head/header"
        )
        return str(json.load(response)["level"])

    # Check if there is already some blockchain data in the tezos-node data directory,
    # and ask the user if it can be overwritten.
    def check_blockchain_data(self):
        node_dir = get_data_dir(self.config["network"])
        node_dir_contents = os.listdir(node_dir)
        clean = ["config.json", "version.json"]
        diff = set(node_dir_contents) - set(clean)
        if diff:
            print("The Tezos node data directory already has some blockchain data:")
            print("\n".join(diff))
            print()
            if yes_or_no("Delete this data and bootstrap the node again? <y/N> ", "no"):
                for path in diff:
                    if proc_call("sudo rm -r " + os.path.join(node_dir, path)):
                        print(
                            "Could not clean the Tezos node data directory. "
                            "Please do so manually."
                        )
                        raise OSError(
                            "'sudo rm -r " + os.path.join(node_dir, path) + "' failed."
                        )

                print("Node directory cleaned.")
                return True
            return False
        return True

    # Importing the snapshot for Node bootstrapping
    def import_snapshot(self):
        do_import = self.check_blockchain_data()
        valid_choice = False

        if do_import:
            self.query_step(history_mode_query)

            proc_call(
                f"sudo -u tezos tezos-node-{self.config['network']} config update "
                f"--history-mode {self.config['history_mode']}"
            )

            if self.config["history_mode"] == "rolling":
                snapshot_import_modes.pop("download full", None)
            else:
                snapshot_import_modes.pop("download rolling", None)
        else:
            return

        while not valid_choice:

            self.query_step(get_snapshot_mode_query(snapshot_import_modes))

            snapshot_file = TMP_SNAPSHOT_LOCATION

            if self.config["snapshot"] == "skip":
                return
            elif self.config["snapshot"] == "file":
                self.query_step(snapshot_file_query)
                if self.config["snapshot_file"] != TMP_SNAPSHOT_LOCATION:
                    snapshot_file = shutil.copyfile(
                        self.config["snapshot_file"], TMP_SNAPSHOT_LOCATION
                    )
            elif self.config["snapshot"] == "url":
                self.query_step(snapshot_url_query)
                url = self.config["snapshot_url"]
                try:
                    snapshot_file = fetch_snapshot(url)
                except ValueError:
                    print()
                    print("The snapshot URL you provided is unavailable.")
                    print("Please check the URL again or choose another option.")
                    print()
                    continue
                except urllib.error.URLError:
                    print()
                    print("The snapshot URL you provided is unavailable.")
                    print("Please check the URL again or choose another option.")
                    print()
                    continue
            elif self.config["snapshot"] == "download rolling":
                url = "https://" + self.config["network"] + ".xtz-shots.io/rolling"
                try:
                    snapshot_file = fetch_snapshot(url)
                except urllib.error.URLError:
                    print()
                    print(
                        "The snapshot download option you chose is unavailable, "
                        "possibly because the protocol is very new."
                    )
                    print(
                        "Please check your internet connection or choose another option."
                    )
                    print()
                    continue
            elif self.config["snapshot"] == "download full":
                url = "https://" + self.config["network"] + ".xtz-shots.io/full"
                try:
                    snapshot_file = fetch_snapshot(url)
                except urllib.error.URLError:
                    print()
                    print(
                        "The snapshot download option you chose is unavailable, "
                        "possibly because the protocol is very new."
                    )
                    print(
                        "Please check your internet connection or choose another option."
                    )
                    print()
                    continue

            valid_choice = True

            import_flag = ""
            if is_full_snapshot(self.config["snapshot"]):
                if self.config["history_mode"] == "archive":
                    import_flag = "--reconstruct "

            proc_call(
                "sudo -u tezos tezos-node-"
                + self.config["network"]
                + " snapshot import "
                + import_flag
                + snapshot_file
            )

            print("Snapshot imported.")

            if self.config["snapshot"] in ["download rolling", "download full", "file"]:
                try:
                    os.remove(TMP_SNAPSHOT_LOCATION)
                except:
                    pass
                else:
                    print("Deleted the temporary snapshot file.")

    # Bootstrapping tezos-node
    def bootstrap_node(self):

        self.import_snapshot()

        print(
            "Starting the node service. This is expected to take some "
            "time, as the node needs a node identity to be generated."
        )

        self.systemctl_start_action("node")

        print("Waiting for the node service to start...")

        while True:
            rpc_address = self.config["node_rpc_addr"]
            try:
                urllib.request.urlopen(rpc_address + "/version")
                break
            except urllib.error.URLError:
                proc_call("sleep 1")

        print("Generated node identity and started the service.")

        self.systemctl_enable()

        if self.config["mode"] == "node":
            print(
                "The node setup is finished. It will take some time for the node to bootstrap.",
                "You can check the progress by running the following command:",
            )
            print(f"systemctl status tezos-node-{self.config['network']}.service")

            print()
            print("Exiting the Tezos Setup Wizard.")
            sys.exit(0)

        print("Waiting for the node to bootstrap...")

        proc_call(
            f"sudo -u tezos {suppress_warning_text} tezos-client "
            f"--endpoint {rpc_address} bootstrapped"
        )

        print()
        print("The Tezos node bootstrapped successfully.")

    # Check if an account with the 'baker' alias already exists, and ask the user
    # if it can be overwritten.
    def check_baker_account(self):
        tezos_client_options = self.get_tezos_client_options()
        baker_alias = self.config["baker_alias"]
        address = get_proc_output(
            f"sudo -u tezos {suppress_warning_text} tezos-client {tezos_client_options} "
            f"show address {baker_alias} --show-secret"
        )
        if address.returncode == 0:
            value_regex = b"(?:" + ledger_regex + b")|(?:" + secret_key_regex + b")"
            value = re.search(value_regex, address.stdout).group(0)
            address = re.search(address_regex, address.stdout).group(0)
            print()
            print("An account with the '" + baker_alias + "' alias already exists.")
            print("Its current value is", value.decode("utf-8"))
            print("With a corresponding address:", address.decode("utf-8"))

            return yes_or_no(
                "Would you like to import a new key and replace this one? <y/N> ", "no"
            )
        else:
            return True

    # Importing the baker key
    def import_baker_key(self):
        baker_alias = self.config["baker_alias"]
        tezos_client_options = self.get_tezos_client_options()
        replace_baker_key = self.check_baker_account()

        if replace_baker_key:
            if self.config["network"] == "mainnet":
                key_import_modes.pop("json", None)

            key_mode_query = get_key_mode_query(key_import_modes)

            valid_choice = False
            while not valid_choice:

                try:
                    self.query_step(key_mode_query)

                    if self.config["key_import_mode"] == "secret-key":
                        self.query_step(secret_key_query)
                        proc_call(
                            f"sudo -u tezos {suppress_warning_text} tezos-client {tezos_client_options} "
                            f"import secret key {baker_alias} {self.config['secret_key']} --force"
                        )
                    elif self.config["key_import_mode"] == "json":
                        self.query_step(json_filepath_query)
                        json_tmp_path = shutil.copy(
                            self.config["json_filepath"], "/tmp/"
                        )
                        proc_call(
                            f"sudo -u tezos {suppress_warning_text} tezos-client {tezos_client_options} "
                            f"activate account {baker_alias} with {json_tmp_path} --force"
                        )
                        try:
                            os.remove(json_tmp_path)
                        except:
                            pass

                    else:
                        print("Please open the Tezos Baking app on your ledger.")
                        (
                            base_ledger_url,
                            ledger_derivations,
                        ) = wait_for_ledger_baking_app()
                        baker_ledger_url = ""
                        while (
                            re.match(ledger_regex.decode("utf-8"), baker_ledger_url)
                            is None
                        ):
                            self.query_step(
                                get_ledger_derivation(
                                    ledger_derivations,
                                    base_ledger_url,
                                    self.config["node_rpc_addr"],
                                )
                            )
                            if self.config["ledger_derivation"] == "Go back":
                                self.import_baker_key()
                                return
                            elif (
                                self.config["ledger_derivation"]
                                == "Specify derivation path"
                            ):
                                self.query_step(derivation_path_query)
                                signing_curves = [
                                    "bip25519",
                                    "ed25519",
                                    "secp256k1",
                                    "P-256",
                                ]
                                for signing_curve in signing_curves:
                                    ledger_derivations.append(
                                        signing_curve
                                        + "/"
                                        + self.config["derivation_path"]
                                    )
                            else:
                                baker_ledger_url = (
                                    base_ledger_url + self.config["ledger_derivation"]
                                )
                        proc_call(
                            f"sudo -u tezos {suppress_warning_text} tezos-client {tezos_client_options} "
                            f"import secret key {baker_alias} {baker_ledger_url} --force"
                        )
                        proc_call(
                            f"sudo -u tezos {suppress_warning_text} tezos-client {tezos_client_options} "
                            f"setup ledger to bake for {baker_alias} --main-hwm {self.get_current_head_level()}"
                        )

                except EOFError:
                    raise EOFError
                except Exception as e:
                    print("Something went wrong when calling tezos-client:")
                    print(str(e))
                    print()
                    print("Please check your input and try again.")
                else:
                    valid_choice = True

    def register_baker(self):
        print()
        tezos_client_options = self.get_tezos_client_options()
        baker_alias = self.config["baker_alias"]
        proc_call(
            f"sudo -u tezos {suppress_warning_text} tezos-client {tezos_client_options} "
            f"register key {baker_alias} as delegate"
        )
        print(
            "You can check a blockchain explorer (e.g. https://tzkt.io/ or https://tzstats.com/)\n"
            "to see the baker status and baking rights of your account."
        )

    def start_baking(self):
        self.systemctl_start_action("baking")

    def systemctl_start_action(self, service):
        proc_call(
            "sudo systemctl start tezos-"
            + service
            + "-"
            + self.config["network"]
            + ".service"
        )

    def systemctl_enable(self):
        if self.config["systemd_mode"] == "yes":
            print(
                "Enabling the tezos-{}-{}.service".format(
                    self.config["mode"], self.config["network"]
                )
            )
            proc_call(
                "sudo systemctl enable tezos-"
                + self.config["mode"]
                + "-"
                + self.config["network"]
                + ".service"
            )
        else:
            print("The services won't restart on boot.")

    def run_setup(self):

        print("Tezos Setup Wizard")
        print()
        print(
            "Welcome, this wizard will help you to set up the infrastructure",
            "to interact with the Tezos blockchain.",
        )
        print(
            "In order to run a baking instance, you'll need the following Tezos binaries:\n",
            "tezos-client, tezos-node, tezos-baker-<proto>, tezos-endorser-<proto>.\n",
            "If you have installed tezos-baking, these binaries are already installed.",
        )
        print("All commands within the service are run under the 'tezos' user.")
        print()
        print(
            "To access help and possible options for each question, type in 'help' or '?'."
        )
        print("Type in 'exit' to quit.")
        print()

        self.query_step(network_query)
        self.fill_baking_config()
        self.query_step(service_mode_query)

        print()
        self.query_step(systemd_mode_query)

        print("Trying to bootstrap tezos-node")
        self.bootstrap_node()

        # If we continue execution here, it means we need to set up baking as well.
        executed = False
        while not executed:
            print()
            print("Importing the baker key")
            self.import_baker_key()

            print()
            print("Registering the baker")
            try:
                self.register_baker()
            except EOFError:
                raise EOFError
            except Exception as e:
                print("Something went wrong when calling tezos-client:")
                print(str(e))
                print()
                print("Going back to the previous step.")
                print("Please check your input and try again.")
                continue
            executed = True

        print()
        print("Starting the baking instance")
        self.start_baking()

        print()
        print(
            "Congratulations! All required Tezos infrastructure services should now be started."
        )
        print(
            "You can show logs for all the services using the 'tezos' user by running:"
        )
        print("journalctl -f _UID=$(id tezos -u)")

        print()
        print("To stop the baking instance, run:")
        print(f"sudo systemctl stop tezos-baking-{self.config['network']}.service")

        print()
        print(
            "If you previously enabled the baking service and want to disable it, run:"
        )
        print(f"sudo systemctl disable tezos-baking-{self.config['network']}.service")


if __name__ == "__main__":
    readline.parse_and_bind("tab: complete")
    readline.set_completer_delims(" ")

    try:
        setup = Setup()
        setup.run_setup()
    except KeyboardInterrupt:
        if "network" in setup.config:
            proc_call(
                "sudo systemctl stop tezos-baking-"
                + setup.config["network"]
                + ".service"
            )
        print("Exiting the Tezos Setup Wizard.")
        sys.exit(1)
    except EOFError:
        if "network" in setup.config:
            proc_call(
                "sudo systemctl stop tezos-baking-"
                + setup.config["network"]
                + ".service"
            )
        print("Exiting the Tezos Setup Wizard.")
        sys.exit(1)
    except Exception as e:
        if "network" in setup.config:
            proc_call(
                "sudo systemctl stop tezos-baking-"
                + setup.config["network"]
                + ".service"
            )
        print("Error in Tezos Setup Wizard, exiting.")
        logfile = "tezos_setup_wizard.log"
        with open(logfile, "a") as f:
            f.write(str(e) + "\n")
        print("The error has been logged to", os.path.abspath(logfile))
        sys.exit(1)
