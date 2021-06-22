#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2021 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ

"""
A wizard utility to help set up tezos-baker.

Asks questions, validates answers, and executes the appropriate steps using the final configuration.
"""

import os, sys, subprocess, shlex
import readline
import re, textwrap
import urllib.request
from typing import List


# Global options

networks = {
    "mainnet": "Main Tezos network",
    "florencenet": "Test network using version 009 of Tezos protocol (Florence)",
    "granadanet": "Test network using version 010 of Tezos protocol (Granada)",
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


# Regexes

ledger_regex = b"ledger:\/\/[\w\-]+\/[\w\-]+\/[\w']+\/[\w']+"
secret_key_regex = b"(encrypted|unencrypted):(?:\w{54}|\w{88})"
address_regex = b"tz1\w{33}"


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


# To be validated, the input should adhere to the ledger URL format:
# ledger://<four mnemonic words separated by dashes>/<curve>/[a-z0-9']+/[a-z0-9']+
def ledger_url_validator(input):
    match = re.match(ledger_regex.decode("utf-8"), input.strip())
    if not bool(match):
        raise ValueError(
            "The input doesn't match the format for the ledger URL: "
            "ledger://<four mnemonic words separated by dashes>/<curve>/[a-z0-9']+/[a-z0-9']+"
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


def proc_call(cmd):
    return subprocess.check_call(shlex.split(cmd))


def fetch_snapshot(url):
    print("Downloading the snapshot from", url)
    filename = "/tmp/tezos_node.snapshot"
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


def list_connected_ledgers():
    output = subprocess.run(
        shlex.split("sudo -u tezos tezos-client list connected ledgers"),
        capture_output=True,
    )
    return [name.decode() for name in re.findall(ledger_regex, output.stdout)]


def get_node_rpc_addr(network):
    output = subprocess.run(
        shlex.split("systemctl show tezos-node-" + network + ".service"),
        capture_output=True,
    ).stdout
    config = re.search(b"Environment=(.*)(?:$|\n)", output)
    if config is None:
        print(
            "tezos-node-" + network + ".service configuration not found, "
            "defaulting to 'http://localhost:8732'"
        )
        return "http://localhost:8732"
    config = config.group(1)
    address = re.search(b"NODE_RPC_ADDR=(.*?)(?: |$|\n)", config)
    if address is not None:
        address = address.group(1).decode("utf-8")
    else:
        print("NODE_RPC_ADDR is undefined, defaulting to 'localhost:8732'")
        address = "localhost:8732"

    mode = "https://"
    if (
        re.search(b"KEY_PATH=(?: |$|\n)", config) is not None
        or re.search(b"CERT_PATH=(?: |$|\n)", config) is not None
    ):
        mode = "http://"

    return mode + address


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
    "The currently supported protocols are 009-PsFLoren (used on florencenet and mainnet)\n"
    "and 010-PtGRANAD (granadanet).\nKeep in mind that you must select the test network "
    "(either florencenet or granadanet) if you plan on baking with a faucet JSON file.",
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

snapshot_mode_query = Step(
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
    "that is sufficient for baking (you can read more about other tezos-node history modes here:\n"
    "https://tezos.gitlab.io/user/history_modes.html#history-modes ).\n",
    options=snapshot_import_modes,
    validator=Validator(enum_range_validator(snapshot_import_modes)),
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

ledger_url_query = Step(
    id="ledger_url",
    prompt="Provide the ledger URL for importing the baker secret key stored on a ledger.\n"
    "You can choose one of the suggested options or provide your own ledger URL.",
    help="Your ledger URL should look something like <ledger://<mnemonic>/ed25519/0'/1'>",
    default=None,
    options=list_connected_ledgers(),
    validator=Validator(
        [
            required_field_validator,
            or_validator(
                enum_range_validator(list_connected_ledgers()), ledger_url_validator
            ),
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

    # Check if there is already some blockchain data in the tezos-node data directory,
    # and ask the user if it can be overwritten.
    def check_blockchain_data(self):
        node_dir = "/var/lib/tezos/node-" + self.config["network"]
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

        while do_import and not valid_choice:

            self.query_step(snapshot_mode_query)

            snapshot_file = ""

            if self.config["snapshot"] == "skip":
                return
            elif self.config["snapshot"] == "file":
                self.query_step(snapshot_file_query)
                snapshot_file = self.config["snapshot_file"]
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

            proc_call(
                "sudo -u tezos tezos-node-"
                + self.config["network"]
                + " snapshot import "
                + snapshot_file
            )

            print("Snapshot imported.")

            if (
                self.config["snapshot"] == "download rolling"
                or self.config["snapshot"] == "download full"
            ):
                try:
                    os.remove("/tmp/tezos_node.snapshot")
                except:
                    pass
                else:
                    print("Deleted the downloaded snapshot.")

    # Bootstrapping tezos-node
    def bootstrap_node(self):

        self.import_snapshot()

        self.systemctl_start_action("node")

        while True:
            rpc_address = get_node_rpc_addr(self.config["network"])
            try:
                urllib.request.urlopen(rpc_address + "/version")
                break
            except urllib.error.URLError:
                print("...Waiting for the node service to start...")
                proc_call("sleep 1")

        proc_call("sudo -u tezos tezos-client bootstrapped")

        print()
        print("The Tezos node bootstrapped successfully.")

    # Check if an account with the 'baker' alias already exists, and ask the user
    # if it can be overwritten.
    def check_baker_account(self):
        address = subprocess.run(
            shlex.split("sudo -u tezos tezos-client show address baker --show-secret"),
            capture_output=True,
        )
        if address.returncode == 0:
            value_regex = b"(?:" + ledger_regex + b")|(?:" + secret_key_regex + b")"
            value = re.search(value_regex, address.stdout).group(0)
            address = re.search(address_regex, address.stdout).group(0)
            print()
            print("An account with the 'baker' alias already exists.")
            print("Its current value is", value.decode("utf-8"))
            print("With a corresponding address:", address.decode("utf-8"))

            return yes_or_no(
                "Would you like to import a new key and replace this one? <y/N> ", "no"
            )
        else:
            return True

    # Importing the baker key
    def import_baker_key(self):

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
                            "sudo -u tezos tezos-client import secret key baker "
                            + self.config["secret_key"]
                            + " --force"
                        )
                    elif self.config["key_import_mode"] == "json":
                        self.query_step(json_filepath_query)
                        proc_call(
                            "sudo -u tezos tezos-client activate account baker with "
                            + self.config["json_filepath"]
                            + " --force"
                        )

                    else:
                        self.query_step(ledger_url_query)

                        print()
                        input(
                            "Please open the Tezos Baking app on your ledger, then hit Enter."
                        )
                        proc_call(
                            "sudo -u tezos tezos-client import secret key baker "
                            + self.config["ledger_url"]
                            + " --force"
                        )
                        proc_call(
                            "sudo -u tezos tezos-client setup ledger to bake for baker"
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
        proc_call("sudo -u tezos tezos-client register key baker as delegate")
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

        print("Tezos Baking Wizard")
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
        self.query_step(service_mode_query)

        print("Trying to bootstrap tezos-node")
        self.bootstrap_node()

        if self.config["mode"] == "baking":
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
        self.query_step(systemd_mode_query)
        self.systemctl_enable()

        print()
        print(
            "Congratulations! All required Tezos infrastructure services should now be started."
        )
        print(
            "You can show logs for all the services using the 'tezos' user by running:"
        )
        print("journalctl -f _UID=$(id tezos -u)")

        if self.config["mode"] == "baking":
            print()
            print("To stop the baking instance, run:")
            print(
                "sudo systemctl stop tezos-baking-"
                + self.config["network"]
                + ".service"
            )

            print()
            print(
                "If you previously enabled the baking service and want to disable it, run:"
            )
            print(
                "sudo systemctl disable tezos-baking-"
                + self.config["network"]
                + ".service"
            )


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
        print("Exiting the Tezos Baking Wizard.")
        sys.exit(1)
    except EOFError:
        if "network" in setup.config:
            proc_call(
                "sudo systemctl stop tezos-baking-"
                + setup.config["network"]
                + ".service"
            )
        print("Exiting the Tezos Baking Wizard.")
        sys.exit(1)
    except Exception as e:
        if "network" in setup.config:
            proc_call(
                "sudo systemctl stop tezos-baking-"
                + setup.config["network"]
                + ".service"
            )
        print("Error in Tezos Baking setup, exiting.")
        logfile = "tezos_baking_wizard.log"
        with open(logfile, "a") as f:
            f.write(str(e) + "\n")
        print("The error has been logged to", os.path.abspath(logfile))
        sys.exit(1)
