# SPDX-FileCopyrightText: 2022 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

"""
Contains shared code from all Tezos wizards for a command line wizard skeleton.

Helps with writing a tool that asks questions, validates answers, and executes
the appropriate steps using the final configuration.
"""

import os, sys, subprocess, shlex, shutil
import re, textwrap
import argparse
import urllib.request
import json

from tezos_baking.util import *
from tezos_baking.validators import Validator
import tezos_baking.validators as validators

# Command line argument parsing


parser = argparse.ArgumentParser()


# Global options

key_import_modes = {
    "ledger": "From a ledger",
    "secret-key": "Either the unencrypted or password-encrypted secret key for your address",
    "remote": "Remote key governed by a signer running on a different machine",
    "generate-fresh-key": "Generate fresh key that should be filled manually later",
    "json": "Faucet JSON file",
}

networks = {
    "mainnet": "Main Tezos network",
    "ghostnet": "Long running test network, currently using the Nairobi Tezos protocol",
    "nairobinet": "Test network using the Nairobi Tezos protocol",
    "oxfordnet": "Test network using the Oxford Tezos protocol",
}

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
            options_count = 0
            for o in self.options:
                if isinstance(o, dict):
                    for values in o.values():
                        if not isinstance(values, list):
                            options_count += 1
                        else:
                            options_count += len(values)
                else:
                    options_count += 1
            index_len = len(str(options_count))
            str_format = f"{{:{index_len}}}. {{}}"
            for o in self.options:
                if isinstance(o, dict):
                    for k, values in o.items():
                        print()
                        print(f"'{k}':")
                        print()
                        if not isinstance(values, list):
                            values = [values]
                        for v in values:
                            if def_i is not None and i == def_i:
                                print(str_format.format(i, "(default) " + v))
                            else:
                                print(str_format.format(i, v))
                            i += 1
                    print()
                else:
                    if def_i is not None and i == def_i:
                        print(str_format.format(i, "(default) " + o))
                    else:
                        print(str_format.format(i, o))
                    i += 1
        elif self.options and isinstance(self.options, dict):
            index_len = len(str(len(self.options)))
            max_option_len = max(map(len, self.options.keys()))
            padding = max(26, max_option_len + 2)
            indent_size = index_len + 4 + padding
            str_format = f"{{:{index_len}}}. {{:<{padding}}}  {{}}"
            for o in self.options:
                description = textwrap.indent(
                    textwrap.fill(self.options[o], 60),
                    " " * indent_size,
                ).lstrip()
                if def_i is not None and i == def_i:
                    print(str_format.format(i, o + " (default)", description))
                else:
                    print(str_format.format(i, o, description))
                i += 1
        elif not self.options and self.default is not None:
            print("Default:", self.default)


# Steps

secret_key_query = Step(
    id="secret_key",
    prompt="Provide either the unencrypted or password-encrypted secret key for your address.",
    help="The format is 'unencrypted:edsk...' for the unencrypted key, or 'encrypted:edesk...'"
    "for the encrypted key.",
    default=None,
    validator=Validator([validators.required_field, validators.secret_key]),
)

remote_signer_uri_query = Step(
    id="remote_signer_uri",
    prompt="Provide your remote key with the address of the signer.",
    help="The format is the address of your remote signer host, followed by a public key,\n"
    "i.e. something like http://127.0.0.1:6732/tz1V8fDHpHzN8RrZqiYCHaJM9EocsYZch5Cy\n"
    "The supported schemes are https, http, tcp, and unix.",
    default=None,
    validator=Validator([validators.required_field, validators.signer_uri]),
)

derivation_path_query = Step(
    id="derivation_path",
    prompt="Provide derivation path for the key stored on the ledger.",
    help="The format is '[0-9]+h/[0-9]+h'",
    default=None,
    validator=Validator([validators.required_field, validators.derivation_path]),
)


json_filepath_query = Step(
    id="json_filepath",
    prompt="Provide the path to your downloaded faucet JSON file.",
    help="The file should contain the 'mnemonic' and 'secret' fields.",
    default=None,
    validator=Validator([validators.required_field, validators.filepath]),
)


def get_ledger_url_query(ledgers):
    return Step(
        id="ledger_url",
        prompt="Choose a ledger to get the new derivation from.",
        options=ledgers,
        default=None,
        validator=Validator(
            [validators.required_field, validators.enum_range(ledgers)]
        ),
        help="In order to specify new derivation path, you need to specify a ledger to get the derivation from.",
    )


# We define this step as a function since the corresponding step requires
# tezos-node to be running and bootstrapped in order to gather the data
# about the ledger-stored addresses, so it's called right before invoking
# after the node was boostrapped
def get_ledger_derivation_query(ledgers_derivations, node_endpoint, client_dir):
    extra_options = ["Specify derivation path", "Go back"]
    full_ledger_urls = []
    for ledger_url, derivations_paths in ledgers_derivations.items():
        for derivation_path in derivations_paths:
            full_ledger_urls.append(ledger_url + derivation_path)
    return Step(
        id="ledger_derivation",
        prompt="Select a key to import from the ledger.\n"
        "You can choose one of the suggested derivations or provide your own:",
        help="'Specify derivation path' will ask a derivation path from you."
        "'Go back' will return you back to the key type choice.",
        default=None,
        options=[ledger_urls_info(ledgers_derivations, node_endpoint, client_dir)]
        + extra_options,
        validator=Validator(
            [
                validators.required_field,
                validators.enum_range(full_ledger_urls + extra_options),
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
                    print(color("Validation error: " + str(e), color_red))
                else:
                    validated = True
                    self.config[step.id] = answer

    def systemctl_simple_action(self, action, service):
        proc_call(
            f"sudo systemctl {action} tezos-{service}-{self.config['network']}.service"
        )

    def systemctl_enable(self):
        if self.config["systemd_mode"] == "yes":
            print(
                "Enabling the tezos-{}-{}.service".format(
                    self.config["mode"], self.config["network"]
                )
            )
            self.systemctl_simple_action("enable", self.config["mode"])
        else:
            print("The services won't restart on boot.")

    def get_tezos_client_options(self):
        options = (
            f"--base-dir {self.config['client_data_dir']} "
            f"--endpoint {self.config['node_rpc_endpoint']}"
        )
        if "remote_host" in self.config:
            options += f" -R '{self.config['remote_host']}'"
        return options

    def query_and_update_config(self, query):
        self.query_step(query)
        self.config["tezos_client_options"] = self.get_tezos_client_options()
        proc_call(
            f"sudo -u tezos {suppress_warning_text} octez-client "
            f"{self.config['tezos_client_options']} config update"
        )

    def fill_baking_config(self):
        net = self.config["network"]
        baking_env = get_systemd_service_env(f"tezos-baking-{net}")

        self.config["client_data_dir"] = baking_env.get(
            "TEZOS_CLIENT_DIR",
            "/var/lib/tezos/.tezos-client",
        )

        node_rpc_addr = baking_env.get(
            "NODE_RPC_ADDR",
            "localhost:8732",
        )
        self.config["node_rpc_addr"] = node_rpc_addr
        self.config["node_rpc_endpoint"] = "http://" + node_rpc_addr

        self.config["baker_alias"] = baking_env.get("BAKER_ADDRESS_ALIAS", "baker")

    def fill_remote_signer_infos(self):
        self.query_step(remote_signer_uri_query)

        rsu = re.search(signer_uri_regex.decode(), self.config["remote_signer_uri"])

        self.config["remote_host"] = rsu.group(1)
        self.config["remote_key"] = rsu.group(2)

    def get_current_head_level(self):
        response = urllib.request.urlopen(
            self.config["node_rpc_endpoint"] + "/chains/main/blocks/head/header"
        )
        return str(json.load(response)["level"])

    # Check if an account with the baker_alias alias already exists, and ask the user
    # if it can be overwritten.
    def check_baker_account(self):
        baker_alias = self.config["baker_alias"]
        baker_key_value = get_key_address(self.get_tezos_client_options(), baker_alias)
        if baker_key_value is not None:
            value, address = baker_key_value
            print()
            print("An account with the '" + baker_alias + "' alias already exists.")
            print("Its current address is", address)

            return yes_or_no(
                "Would you like to import a new key and replace this one? <y/N> ", "no"
            )
        else:
            return True

    def import_key(self, key_mode_query, ledger_app=None):

        baker_alias = self.config["baker_alias"]
        tezos_client_options = self.get_tezos_client_options()

        valid_choice = False
        while not valid_choice:

            try:
                self.query_step(key_mode_query)

                if self.config["key_import_mode"] == "secret-key":
                    self.query_step(secret_key_query)
                    proc_call(
                        f"sudo -u tezos {suppress_warning_text} octez-client {tezos_client_options} "
                        f"import secret key {baker_alias} {self.config['secret_key']} --force"
                    )
                elif self.config["key_import_mode"] == "remote":
                    self.fill_remote_signer_infos()

                    tezos_client_options = self.get_tezos_client_options()
                    proc_call(
                        f"sudo -u tezos {suppress_warning_text} octez-client {tezos_client_options} "
                        f"import secret key {baker_alias} remote:{self.config['remote_key']} --force"
                    )
                elif self.config["key_import_mode"] == "generate-fresh-key":
                    proc_call(
                        f"sudo -u tezos {suppress_warning_text} octez-client {tezos_client_options} "
                        f"gen keys {baker_alias} --force"
                    )
                    print("Newly generated baker key:")
                    proc_call(
                        f"sudo -u tezos {suppress_warning_text} octez-client {tezos_client_options} "
                        f"show address {baker_alias}"
                    )
                    network = self.config["network"]
                    print(
                        f"Before proceeding with baker registration you'll need to provide this address with some XTZ.\n"
                        f"Note that you need at least 6000 XTZ in order to receive baking and endorsing rights.\n"
                        f"You can fill your address using the faucet: https://faucet.{network}.teztnets.xyz/.\n"
                        f"Waiting for funds to arrive... (Ctrl + C to choose another option)."
                    )
                    try:
                        while True:
                            result = get_proc_output(
                                f"sudo -u tezos {suppress_warning_text} octez-client {tezos_client_options} "
                                f"register key {baker_alias} as delegate"
                            )
                            if result.returncode == 0:
                                print(result.stdout.decode("utf8"))
                                break
                            else:
                                proc_call("sleep 1")
                    except KeyboardInterrupt:
                        print("Going back to the import mode selection.")
                        continue
                elif self.config["key_import_mode"] == "json":
                    self.query_step(json_filepath_query)
                    json_tmp_path = shutil.copy(self.config["json_filepath"], "/tmp/")
                    proc_call(
                        f"sudo -u tezos {suppress_warning_text} octez-client {tezos_client_options} "
                        f"activate account {baker_alias} with {json_tmp_path} --force"
                    )
                    try:
                        os.remove(json_tmp_path)
                    except:
                        pass
                else:
                    print(f"Please open the Tezos {ledger_app} app on your ledger or")
                    print("press Ctrl+C to go back to the key import mode selection.")
                    ledgers_derivations = wait_for_ledger_app(
                        ledger_app, self.config["client_data_dir"]
                    )
                    if ledgers_derivations is None:
                        print("Going back to the import mode selection.")
                        continue
                    ledgers = list(ledgers_derivations.keys())
                    baker_ledger_url = ""
                    while re.match(ledger_regex.decode(), baker_ledger_url) is None:
                        self.query_step(
                            get_ledger_derivation_query(
                                ledgers_derivations,
                                self.config["node_rpc_endpoint"],
                                self.config["client_data_dir"],
                            )
                        )
                        if self.config["ledger_derivation"] == "Go back":
                            self.import_key(key_mode_query, ledger_app)
                            return
                        elif (
                            self.config["ledger_derivation"]
                            == "Specify derivation path"
                        ):
                            if len(ledgers) >= 1:
                                # If there is only one connected ledger, there is nothing to choose from
                                if len(ledgers) == 1:
                                    ledger_url = ledgers[0]
                                else:
                                    self.query_step(get_ledger_url_query(ledgers))
                                    ledger_url = self.config["ledger_url"]
                                self.query_step(derivation_path_query)
                                signing_curves = [
                                    "bip25519",
                                    "ed25519",
                                    "secp256k1",
                                    "P-256",
                                ]
                                for signing_curve in signing_curves:
                                    ledgers_derivations.setdefault(
                                        ledger_url, []
                                    ).append(
                                        signing_curve
                                        + "/"
                                        + self.config["derivation_path"]
                                    )
                        else:
                            baker_ledger_url = self.config["ledger_derivation"]
                    proc_call(
                        f"sudo -u tezos {suppress_warning_text} octez-client {tezos_client_options} "
                        f"import secret key {baker_alias} {baker_ledger_url} --force"
                    )

            except EOFError:
                raise EOFError
            except Exception as e:
                print("Something went wrong when calling octez-client:")
                print(str(e))
                print()
                print("Please check your input and try again.")
            else:
                valid_choice = True
                value, _ = get_key_address(
                    tezos_client_options, self.config["baker_alias"]
                )
                self.config["baker_key_value"] = value
