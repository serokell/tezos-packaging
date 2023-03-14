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
import traceback
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

systemd_enable = {
    "yes": "Enable the services, running them both now and on every boot",
    "no": "Start the services this time only",
}

history_modes = {
    "rolling": "Store a minimal rolling window of chain data, lightest option",
    "full": "Store enough chain data to reconstruct the complete chain state",
    "archive": "Store all the chain data, very storage-demanding",
}

toggle_vote_modes = {
    "pass": "Abstain from voting",
    "off": "Request to end the subsidy",
    "on": "Request to continue or restart the subsidy",
}


TMP_SNAPSHOT_LOCATION = "/tmp/octez_node.snapshot"


# Wizard CLI utility


welcome_text = """Tezos Setup Wizard

Welcome, this wizard will help you to set up the infrastructure to interact with the
Tezos blockchain.

In order to run a baking instance, you'll need the following Tezos packages:
 tezos-client, tezos-node, tezos-baker-<proto>.
If you have installed tezos-baking, these packages are already installed.

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
            "sudo -u tezos octez-node snapshot info " + TMP_SNAPSHOT_LOCATION
        ).stdout
        return re.search(b"at level [0-9]+ in full", output) is not None
    return False


# Steps

network_query = Step(
    id="network",
    prompt="Which Tezos network would you like to use?\nCurrently supported:",
    help="The selected network will be used to set up all required services.\n"
    "The currently supported protocol is `PtLimaPt` (used on `limanet`, `ghostnet` and `mainnet`) and `PtMumbai` (used on `mumbainet`).\n"
    "Keep in mind that you must select the test network (e.g. limanet)\n"
    "if you plan on baking with a faucet JSON file.\n",
    options=networks,
    validator=Validator(enum_range_validator(networks)),
)

service_mode_query = Step(
    id="mode",
    prompt="Do you want to set up baking or to run the standalone node?",
    help="By default, tezos-baking provides predefined services for running baking instances "
    "on different networks.\nSometimes, however, you might want to only run the Tezos node.\n"
    "When this option is chosen, this wizard will help you bootstrap the Tezos node only.",
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

liquidity_toggle_vote_query = Step(
    id="liquidity_toggle_vote",
    prompt="Would you like to request to end the Liquidity Baking subsidy?",
    help="Tezos chain offers a Liquidity Baking subsidy mechanism to incentivise exchange\n"
    "between tez and tzBTC. You can ask to end this subsidy, ask to continue it, or abstain.\n"
    "\nYou can read more about this in the here:\n"
    "https://tezos.gitlab.io/active/liquidity_baking.html",
    options=toggle_vote_modes,
    validator=Validator(enum_range_validator(toggle_vote_modes)),
)

# We define this step as a function to better tailor snapshot options to the chosen history mode
def get_snapshot_mode_query(modes):
    return Step(
        id="snapshot",
        prompt="The Tezos node can take a significant time to bootstrap from scratch.\n"
        "Bootstrapping from a snapshot is suggested instead.\n"
        "How would you like to proceed?",
        help="A fully-synced local Tezos node is required for running a baking instance.\n"
        "By default, the Tezos node service will start to bootstrap from scratch,\n"
        "which will take a significant amount of time.\nIn order to avoid this, we suggest "
        "bootstrapping from a snapshot instead.\n\n"
        "Snapshots can be downloaded from the following websites:\n"
        "Tezos Giganode Snapshots - https://snapshots-tezos.giganode.io/ \n"
        "XTZ-Shots - https://xtz-shots.io/ \n\n"
        "We recommend to use rolling snapshots. This is the smallest and the fastest mode\n"
        "that is sufficient for baking. You can read more about other Tezos node history modes here:\n"
        "https://tezos.gitlab.io/user/history_modes.html#history-modes",
        options=modes,
        validator=Validator(enum_range_validator(modes)),
    )


snapshot_file_query = Step(
    id="snapshot_file",
    prompt="Provide the path to the node snapshot file.",
    help="You have indicated wanting to import the snapshot from a file.\n"
    "You can download the snapshot yourself e.g. from XTZ-Shots or Tezos Giganode Snapshots.",
    default=None,
    validator=Validator([required_field_validator, filepath_validator]),
)

snapshot_url_query = Step(
    id="snapshot_url",
    prompt="Provide the url of the node snapshot file.",
    help="You have indicated wanting to import the snapshot from a custom url.\n"
    "You can use e.g. links to XTZ-Shots or Tezos Giganode Snapshots resources.",
    default=None,
    validator=Validator([required_field_validator, reachable_url_validator()]),
)

history_mode_query = Step(
    id="history_mode",
    prompt="Which history mode do you want your node to run in?",
    help="History modes govern how much data a Tezos node stores, and, consequently, how much disk\n"
    "space is required. Rolling mode is the smallest and fastest but still sufficient for baking.\n"
    "You can read more about different nodes history modes here:\n"
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
    # Check if there is already some blockchain data in the octez-node data directory,
    # and ask the user if it can be overwritten.
    def check_blockchain_data(self):
        node_dir = get_data_dir(self.config["network"])
        node_dir_contents = set()
        try:
            node_dir_contents = set(os.listdir(node_dir))
        except FileNotFoundError:
            print("The Tezos node data directory does not exist.")
            print("  Creating directory: " + node_dir)
            proc_call("sudo mkdir " + node_dir)
            proc_call("sudo chown tezos:tezos " + node_dir)

        # Content expected in a configured and clean node data dir
        node_dir_config = set(["config.json", "version.json"])

        # Configure data dir if the config is missing
        if not node_dir_config.issubset(node_dir_contents):
            print("The Tezos node data directory has not been configured yet.")
            print("  Configuring directory: " + node_dir)
            proc_call(
                "sudo -u tezos octez-node-"
                + self.config["network"]
                + " config init"
                + " --network "
                + self.config["network"]
                + " --rpc-addr "
                + self.config["node_rpc_addr"]
            )

        diff = node_dir_contents - node_dir_config
        if diff:
            print("The Tezos node data directory already has some blockchain data:")
            print("\n".join(["- " + os.path.join(node_dir, path) for path in diff]))
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

    # Check https://xtz-shots.io/tezos-snapshots.json and collect the most recent snapshot
    # that is suited for the chosen history mode and network
    def get_snapshot_link(self):
        self.config["snapshot_url"] = None
        self.config["snapshot_block_hash"] = None

        json_url = "https://xtz-shots.io/tezos-snapshots.json"
        try:
            snapshot_array = None
            with urllib.request.urlopen(json_url) as url:
                snapshot_array = json.load(url)["data"]
            snapshot_array.sort(reverse=True, key=lambda x: x["block_height"])

            snapshot_metadata = next(
                filter(
                    lambda artifact: artifact["artifact_type"] == "tezos-snapshot"
                    and artifact["chain_name"] == self.config["network"]
                    and (
                        artifact["history_mode"] == self.config["history_mode"]
                        or (
                            self.config["history_mode"] == "archive"
                            and artifact["history_mode"] == "full"
                        )
                    ),
                    iter(snapshot_array),
                ),
                {"url": None, "block_hash": None},
            )

            self.config["snapshot_url"] = snapshot_metadata["url"]
            self.config["snapshot_block_hash"] = snapshot_metadata["block_hash"]
        except (urllib.error.URLError, ValueError):
            print(f"Couldn't collect snapshot metadata from {json_url}")
        except Exception as e:
            print(f"Unexpected error handling snapshot metadata:\n{e}\n")

    # Importing the snapshot for Node bootstrapping
    def import_snapshot(self):
        do_import = self.check_blockchain_data()
        valid_choice = False

        if do_import:
            self.query_step(history_mode_query)

            proc_call(
                f"sudo -u tezos octez-node-{self.config['network']} config update "
                f"--history-mode {self.config['history_mode']}"
            )

            self.get_snapshot_link()

            if self.config["snapshot_url"] is None:
                snapshot_import_modes.pop("download rolling", None)
                snapshot_import_modes.pop("download full", None)
            elif self.config["history_mode"] == "rolling":
                snapshot_import_modes.pop("download full", None)
            else:
                snapshot_import_modes.pop("download rolling", None)

        else:
            return

        while not valid_choice:

            self.query_step(get_snapshot_mode_query(snapshot_import_modes))

            snapshot_file = TMP_SNAPSHOT_LOCATION
            snapshot_block_hash = None

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
                try:
                    snapshot_file = fetch_snapshot(self.config["snapshot_url"])
                except (ValueError, urllib.error.URLError):
                    print()
                    print("The snapshot URL you provided is unavailable.")
                    print("Please check the URL again or choose another option.")
                    print()
                    continue
            else:
                url = self.config["snapshot_url"]
                snapshot_block_hash = self.config["snapshot_block_hash"]
                try:
                    snapshot_file = fetch_snapshot(url)
                except (ValueError, urllib.error.URLError):
                    print()
                    print("The snapshot download option you chose is unavailable,")
                    print("which normally shouldn't happen. Please check your")
                    print("internet connection or choose another option.")
                    print()
                    continue

            valid_choice = True

            import_flag = ""
            if is_full_snapshot(self.config["snapshot"]):
                if self.config["history_mode"] == "archive":
                    import_flag = "--reconstruct "

            block_hash_option = ""
            if snapshot_block_hash is not None:
                block_hash_option = " --block " + snapshot_block_hash

            proc_call(
                "sudo -u tezos octez-node-"
                + self.config["network"]
                + " snapshot import "
                + import_flag
                + snapshot_file
                + block_hash_option
            )

            print("Snapshot imported.")

            try:
                os.remove(TMP_SNAPSHOT_LOCATION)
            except:
                pass
            else:
                print("Deleted the temporary snapshot file.")

    # Bootstrapping octez-node
    def bootstrap_node(self):

        self.import_snapshot()

        print(
            "Starting the node service. This is expected to take some "
            "time, as the node needs a node identity to be generated."
        )

        self.systemctl_simple_action("start", "node")

        print("Waiting for the node service to start...")

        while True:
            rpc_endpoint = self.config["node_rpc_endpoint"]
            try:
                urllib.request.urlopen(rpc_endpoint + "/version")
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

        tezos_client_options = self.get_tezos_client_options()
        proc_call(
            f"sudo -u tezos {suppress_warning_text} octez-client {tezos_client_options} bootstrapped"
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
                key_import_modes.pop("generate-fresh-key", None)
            key_mode_query = get_key_mode_query(key_import_modes)

            baker_set_up = False
            while not baker_set_up:
                self.import_key(key_mode_query, "Baking")

                if self.config["key_import_mode"] == "ledger":
                    try:
                        proc_call(
                            f"sudo -u tezos {suppress_warning_text} octez-client {tezos_client_options} "
                            f"setup ledger to bake for {baker_alias} --main-hwm {self.get_current_head_level()}"
                        )
                        baker_set_up = True
                    except PermissionError:
                        print("Going back to the import mode selection.")
                else:
                    baker_set_up = True

    def register_baker(self):
        print()
        tezos_client_options = self.get_tezos_client_options()
        baker_alias = self.config["baker_alias"]
        proc_call(
            f"sudo -u tezos {suppress_warning_text} octez-client {tezos_client_options} "
            f"register key {baker_alias} as delegate"
        )
        print(
            "You can check a blockchain explorer (e.g. https://tzkt.io/ or https://tzstats.com/)\n"
            "to see the baker status and baking rights of your account."
        )

    # There is no changing the toggle vote option at a glance,
    # so we need to change the config every time
    def set_liquidity_toggle_vote(self):
        self.query_step(liquidity_toggle_vote_query)

        net = self.config["network"]
        replace_systemd_service_env(
            f"tezos-baking-{net}",
            "LIQUIDITY_BAKING_TOGGLE_VOTE",
            f"\"{self.config['liquidity_toggle_vote']}\"",
        )

    def start_baking(self):
        self.systemctl_simple_action("restart", "baking")

    def run_setup(self):

        print(welcome_text)

        self.query_step(network_query)
        self.fill_baking_config()
        self.query_step(service_mode_query)

        print()
        self.query_step(systemd_mode_query)

        print("Trying to bootstrap octez-node")
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
                print("Something went wrong when calling octez-client:")
                print(str(e))
                print()
                print("Going back to the previous step.")
                print("Please check your input and try again.")
                continue
            executed = True

        self.set_liquidity_toggle_vote()

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
        logfile = "tezos_setup.log"
        with open(logfile, "a") as f:
            f.write(traceback.format_exc() + "\n")
        print("The error has been logged to", os.path.abspath(logfile))
        sys.exit(1)


if __name__ == "__main__":
    main()
