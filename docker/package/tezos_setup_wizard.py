#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2021 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

"""
A wizard utility to help set up tezos-baker.

Asks questions, validates answers, and executes the appropriate steps using the final configuration.
"""

import os, sys, shutil
import readline
import re
import urllib.request
import json
from typing import List

from .wizard_structure import *

# Global options

modes = {
    "baking": "Set up and start all services for baking: "
    "tezos-node and tezos-baker.",
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
    "remote": "Remote key governed by a signer running on a different machine",
    "json": "Faucet JSON file from https://teztnets.xyz/",
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


# Wizard CLI utility


welcome_text = """Tezos Setup Wizard

Welcome, this wizard will help you to set up the infrastructure to interact with the
Tezos blockchain.

In order to run a baking instance, you'll need the following Tezos binaries:
 tezos-client, tezos-node, tezos-baker-<proto>.
If you have installed tezos-baking, these binaries are already installed.

All commands within the service are run under the 'tezos' user.

To access help and possible options for each question, type in 'help' or '?'.
Type in 'exit' to quit.
"""


def fetch_snapshot(url):
    print("Downloading the snapshot from", url)
    filename = TMP_SNAPSHOT_LOCATION
    urllib.request.urlretrieve(url, filename, progressbar_hook)
    print()
    return filename


def is_full_snapshot(import_mode):
    if import_mode == "download full":
        return True
    if import_mode == "file" or import_mode == "url":
        output = get_proc_output(
            "sudo -u tezos tezos-node snapshot info " + TMP_SNAPSHOT_LOCATION
        ).stdout
        return re.search(b"at level [0-9]+ in full", output) is not None
    return False


# Steps

network_query = Step(
    id="network",
    prompt="Which Tezos network would you like to use?\nCurrently supported:",
    help="The selected network will be used to set up all required services.\n"
    "The currently supported protocol are 012-Psithaca (used on ithacanet and mainnet)\n"
    "and 012-PtJakart (used on jakartanet).\n"
    "Keep in mind that you must select the test network (ithacanet or jakartanet)\n"
    "if you plan on baking with a faucet JSON file.\n",
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
    default=None,
    validator=Validator([required_field_validator, filepath_validator]),
)

snapshot_url_query = Step(
    id="snapshot_url",
    prompt="Provide the url of the tezos-node snapshot file.",
    help="You have indicated wanting to import the snapshot from a custom url.\n"
    "You can use e.g. links to XTZ-Shots or Tezos Giganode Snapshots resources.",
    default=None,
    validator=Validator([required_field_validator, reachable_url_validator()]),
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


class Setup(Setup):
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
                    try:
                        proc_call("sudo rm -r " + os.path.join(node_dir, path))
                    except:
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
                except (ValueError, urllib.error.URLError):
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

    # Importing the baker key
    def import_baker_key(self):
        baker_alias = self.config["baker_alias"]
        tezos_client_options = self.get_tezos_client_options()
        replace_baker_key = self.check_baker_account()

        if replace_baker_key:
            if self.config["network"] == "mainnet":
                key_import_modes.pop("json", None)

            key_mode_query = get_key_mode_query(key_import_modes)

            self.import_key(key_mode_query, "Baking")

            proc_call(
                f"sudo -u tezos {suppress_warning_text} tezos-client {tezos_client_options} "
                f"setup ledger to bake for {baker_alias} --main-hwm {self.get_current_head_level()}"
            )

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

    def run_setup(self):

        print(welcome_text)

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


def main():
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


if __name__ == "__main__":
    main()
