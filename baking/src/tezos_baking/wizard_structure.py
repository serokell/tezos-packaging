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
import logging
from logging.handlers import RotatingFileHandler
import urllib.request
import json

from tezos_baking.util import *
from tezos_baking.validators import Validator
import tezos_baking.validators as validators
from tezos_baking.steps import *

# Command line argument parsing

parser = argparse.ArgumentParser()

# Wizard CLI skeleton


def get_data_dir(network):
    logging.info("Getting node data dir")
    node_env = get_systemd_service_env(f"tezos-node-{network}")
    data_dir = node_env.get("TEZOS_NODE_DIR")
    if data_dir is None:
        print_and_log(
            "TEZOS_NODE_DIR is undefined, defaulting to /var/lib/tezos/node-" + network
        )
        return "/var/lib/tezos/node-" + network
    return data_dir


def get_key_address(tezos_client_options, key_alias):
    logging.info("Getting the secret key address")
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


def search_json_with_default(json_filepath, field, default):
    with open(json_filepath, "r") as f:
        try:
            json_dict = json.load(f)
        except:
            return default
        return json_dict.pop(field, default)


def setup_logger(log_file):
    log_dir = f"{os.getenv('HOME')}/.tezos-logs/.debug"
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, log_file)
    logging.basicConfig(
        handlers=[RotatingFileHandler(log_file, maxBytes=4000, backupCount=10)],
        level=logging.DEBUG,
        format="%(asctime)s|%(levelname)s|%(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
        encoding="utf-8",
    )


def print_and_log(message, log=logging.info, colorcode=None):
    print(color(message, colorcode) if colorcode else message)
    log(message)


def log_exception(exception, logfile):
    import traceback
    from datetime import datetime

    logging.error(f"{str(exception)}")

    error_output = traceback.format_exc()

    print("\nHere are last 10 lines of the error output:")
    print("\n".join(error_output.splitlines()[-9:]))

    log_dir = f".tezos-logs/"

    with open(os.path.join(os.getenv("HOME"), log_dir, logfile), "a") as f:
        f.write(datetime.now().strftime("%H:%M:%S %d/%m/%Y:"))
        f.write("\n")
        f.write(error_output)
        f.write("\n")

    print(
        "\nThe error has been logged to the log file:",
        os.path.join("~", log_dir, logfile),
    )
    print("To see the full log, please run:")
    print(f"> cat {os.path.join('~', log_dir, logfile)}")


class Setup:
    def __init__(self, config={}):
        self.config = config

    def query_step(self, step: Step):
        validated = False
        logging.info(f"Querying step: {step.id}")
        while not validated:
            print(step.prompt)
            step.pprint_options()
            answer = input("> ").strip()

            logging.info(f"Supplied answer: {answer}")

            if answer.lower() in ["quit", "exit"]:
                raise KeyboardInterrupt
            elif answer.lower() in ["help", "?"]:
                print(step.help)
                print()
            else:
                if not answer and step.default is not None:
                    logging.info(f"Used default value: {step.default}")
                    answer = step.default

                try:
                    if step.validator is not None:
                        answer = step.validator.validate(answer)
                except ValueError as e:
                    print(color("Validation error: " + str(e), color_red))
                    logging.error(f"Validation error: {e}")
                else:
                    validated = True
                    logging.info("Answer is validated.")
                    self.config[step.id] = answer

        logging.info(f"config|{step.id}|{self.config[step.id]}")

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
        logging.info("Updating octez-node config")
        proc_call(
            f"sudo -u tezos {suppress_warning_text} octez-client "
            f"{self.config['tezos_client_options']} config update"
        )

    def fill_baking_config(self):
        logging.info("Filling in baking config...")
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
        logging.info("Checking baker account")
        baker_alias = self.config["baker_alias"]
        baker_key_value = get_key_address(self.get_tezos_client_options(), baker_alias)
        if baker_key_value is not None:
            value, address = baker_key_value
            print()
            print_and_log(
                "An account with the '" + baker_alias + "' alias already exists."
            )
            print("Its current address is", address)

            self.query_step(replace_key_query)
            return self.config["replace_key"] == "yes"
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
                    logging.info("Importing secret key")
                    proc_call(
                        f"sudo -u tezos {suppress_warning_text} octez-client {tezos_client_options} "
                        f"import secret key {baker_alias} {self.config['secret_key']} --force"
                    )
                elif self.config["key_import_mode"] == "remote":
                    self.fill_remote_signer_infos()

                    tezos_client_options = self.get_tezos_client_options()
                    logging.info("Importing remote secret key")
                    proc_call(
                        f"sudo -u tezos {suppress_warning_text} octez-client {tezos_client_options} "
                        f"import secret key {baker_alias} remote:{self.config['remote_key']} --force"
                    )
                elif self.config["key_import_mode"] == "generate-fresh-key":
                    logging.info("Generating secret key")
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
                    logging.info("Waiting for funds to arrive")
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
                        logging.error("Got keyboard interrupt")
                        print("Going back to the import mode selection.")
                        continue
                elif self.config["key_import_mode"] == "json":
                    self.query_step(json_filepath_query)
                    logging.info("Importing json faucet file")
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
                    print(
                        color(
                            f"Waiting for the Tezos {ledger_app} to be opened...",
                            color_green,
                        ),
                        end="",
                        flush=True,
                    )
                    logging.info("Waiting for ledger derivations list")
                    ledgers_derivations = wait_for_ledger_app(
                        ledger_app, self.config["client_data_dir"]
                    )
                    print()
                    if ledgers_derivations is None:
                        logging.error("Ledger derivations list is empty")
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
                            logging.info("Restarting import key procedure")
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
                    print(
                        color(
                            "Waiting for your response to the prompt on your Ledger Device...",
                            color_green,
                        )
                    )
                    logging.info("Importing secret key")
                    proc_call(
                        f"sudo -u tezos {suppress_warning_text} octez-client {tezos_client_options} "
                        f"import secret key {baker_alias} {baker_ledger_url} --force"
                    )

            except EOFError:
                logging.error("Got EOF")
                raise EOFError
            except Exception as e:
                print_and_log(
                    "Something went wrong when calling octez-client:", logging.error
                )
                print_and_log(str(e), logging.error)
                print()
                print("Please check your input and try again.")
            else:
                valid_choice = True
                value, _ = get_key_address(
                    tezos_client_options, self.config["baker_alias"]
                )
                self.config["baker_key_value"] = value
