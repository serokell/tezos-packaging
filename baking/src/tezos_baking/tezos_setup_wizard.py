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
import time
import urllib.request
import json
from typing import List
import logging

from tezos_baking.wizard_structure import *
from tezos_baking.util import *
from tezos_baking.steps import *
from tezos_baking.provider import *
from tezos_baking.validators import Validator
import tezos_baking.validators as validators

# Global options

modes = {
    "baking": "Set up and start all services for baking: "
    "tezos-node and tezos-baker.",
    "node": "Only bootstrap and run the Tezos node.",
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

TMP_SNAPSHOT_LOCATION = "/tmp/octez_node.snapshot.d/"


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


class Sha256Mismatch(Exception):
    "Raised when the actual and expected sha256 don't match."

    def __init__(self, actual_sha256=None, expected_sha256=None):
        self.actual_sha256 = actual_sha256
        self.expected_sha256 = expected_sha256


class InterruptStep(Exception):
    "Raised when there is need to interrupt step handling flow."


def check_file_contents_integrity(filename, sha256):
    import hashlib

    sha256sum = hashlib.sha256()
    with open(filename, "rb") as f:
        contents = f.read()
    sha256sum.update(contents)

    actual_sha256 = str(sha256sum.hexdigest())
    expected_sha256 = sha256

    if actual_sha256 != expected_sha256:
        raise Sha256Mismatch(actual_sha256, expected_sha256)


def is_full_snapshot(snapshot_file, import_mode):
    if import_mode == "download full":
        return True
    if import_mode == "file" or import_mode == "url":
        output = get_proc_output(
            "sudo -u tezos octez-node snapshot info " + snapshot_file
        ).stdout
        return re.search(b"at level [0-9]+ in full", output) is not None
    return False


def is_non_protocol_testnet(network):
    return network == "mainnet" or network == "ghostnet"


# Starting from Nairobi protocol, the corresponding testnet
# is no longer a named network, so we need to provide the URL
# of the network configuration instead of the network name
# in 'octez-node config init' command.
def network_name_or_teztnets_url(network):
    if is_non_protocol_testnet(network):
        return network
    else:
        return f"https://teztnets.com/{network}"


# Steps

network_query = Step(
    id="network",
    prompt="Which Tezos network would you like to use?\nCurrently supported:",
    help="The selected network will be used to set up all required services.\n"
    "The currently supported protocol is Proxford (used on `oxfordnet`, `ghostnet` and `mainnet`) and PtParisB (used on `paris2net`).\n"
    "Keep in mind that you must select the test network (e.g. ghostnet)\n"
    "if you plan on baking with a faucet JSON file.\n",
    options=networks,
    validator=Validator(validators.enum_range(networks)),
)

service_mode_query = Step(
    id="mode",
    prompt="Do you want to set up baking or to run the standalone node?",
    help="By default, tezos-baking provides predefined services for running baking instances "
    "on different networks.\nSometimes, however, you might want to only run the Tezos node.\n"
    "When this option is chosen, this wizard will help you bootstrap the Tezos node only.",
    options=modes,
    validator=Validator(validators.enum_range(modes)),
)

systemd_mode_query = Step(
    id="systemd_mode",
    prompt="Would you like your setup to automatically start on boot?",
    help="Starting the service will make it available just for this session, great\n"
    "if you want to experiment. Enabling it will make it start on every boot.",
    options=systemd_enable,
    validator=Validator(validators.enum_range(systemd_enable)),
)

liquidity_toggle_vote_query = Step(
    id="liquidity_toggle_vote",
    prompt="Would you like to request to end the Liquidity Baking subsidy?",
    help="Tezos chain offers a Liquidity Baking subsidy mechanism to incentivise exchange\n"
    "between tez and tzBTC. You can ask to end this subsidy, ask to continue it, or abstain.\n"
    "\nYou can read more about this in the here:\n"
    "https://tezos.gitlab.io/active/liquidity_baking.html",
    options=toggle_vote_modes,
    validator=Validator(validators.enum_range(toggle_vote_modes)),
)

regions = {
    "eu": "European region",
    "us": "US region",
    "asia": "Asian region",
}

region_step = Step(
    id="region",
    prompt="Choose the snapshot service closest to your servers:",
    help="Snapshot download can take significant time to finish.\n"
    "Choosing correct region will provide you better download speed.",
    options=regions,
    validator=Validator(validators.enum_range(regions)),
)

# We define this step as a function to better tailor snapshot options to the chosen history mode
def get_snapshot_mode_query(config):

    static_import_modes = {
        "file": "Import snapshot from a file",
        "direct url": "Import snapshot from a direct url",
        "provider url": "Import snapshot from a provider",
        "skip": "Skip snapshot import and synchronize with the network from scratch",
    }

    history_mode = config["history_mode"]

    mk_option = lambda pr, hm=history_mode: f"download {hm} ({pr})"
    mk_desc = lambda pr, hm=history_mode: f"Import {hm} snapshot from {pr}" + (
        " (recommended)" if pr == recommended_provider else ""
    )

    dynamic_import_modes = {}

    for provider in default_providers:
        dynamic_import_modes[mk_option(provider.title)] = mk_desc(provider.title)

    import_modes = {**dynamic_import_modes, **static_import_modes}

    return Step(
        id="snapshot_mode",
        prompt="The Tezos node can take a significant time to bootstrap from scratch.\n"
        "Bootstrapping from a snapshot is suggested instead.\n"
        "How would you like to proceed?",
        help="A fully-synced local Tezos node is required for running a baking instance.\n"
        "By default, the Tezos node service will start to bootstrap from scratch,\n"
        "which will take a significant amount of time.\nIn order to avoid this, we suggest "
        "bootstrapping from a snapshot instead.\n\n"
        "Snapshots can be downloaded from the following websites:\n"
        "Tzinit - https://snapshots.tzinit.org/ \n\n"
        "Marigold - https://snapshots.tezos.marigold.dev/ \n"
        "We recommend to use rolling snapshots. This is the smallest and the fastest mode\n"
        "that is sufficient for baking. You can read more about other Tezos node history modes here:\n"
        "https://tezos.gitlab.io/user/history_modes.html#history-modes",
        options=import_modes,
        validator=Validator(validators.enum_range(import_modes)),
    )


delete_node_data_options = {
    "no": "Keep the existing data",
    "yes": "Remove the data under the tezos node data directory",
}

delete_node_data_query = Step(
    id="delete_node_data",
    prompt="Delete this data and bootstrap the node again?",
    help="It's possible to proceed with bootstrapping the node using\n"
    "the existing blockchain data, instead of importing fresh snapshot.",
    options=delete_node_data_options,
    validator=Validator(validators.enum_range(delete_node_data_options)),
)

snapshot_file_query = Step(
    id="snapshot_file",
    prompt="Provide the path to the node snapshot file.",
    help="You have indicated wanting to import the snapshot from a file.\n"
    "You can download the snapshot yourself e.g. from Tzinit or Tezos Giganode Snapshots.",
    default=None,
    validator=Validator([validators.required_field, validators.filepath]),
)

provider_url_query = Step(
    id="provider_url",
    prompt="Provide the url of the snapshot provider.",
    help="You have indicated wanting to fetch the snapshot from a custom provider.\n",
    default=None,
    validator=Validator([validators.required_field, validators.reachable_url()]),
)

snapshot_url_query = Step(
    id="snapshot_url",
    prompt="Provide the url of the node snapshot file.",
    help="You have indicated wanting to import the snapshot from a custom url.\n"
    "You can use e.g. links to Tzinit or Marigold resources.",
    default=None,
    validator=Validator([validators.required_field, validators.reachable_url()]),
)

snapshot_sha256_query = Step(
    id="snapshot_sha256",
    prompt="Provide the sha256 of the node snapshot file. (optional)",
    help="With sha256 provided, an integrity check will be performed for you.\n"
    "Also, it will be possible to resume incomplete snapshot downloads.",
    default=None,
)

history_mode_query = Step(
    id="history_mode",
    prompt="Which history mode do you want your node to run in?",
    help="History modes govern how much data a Tezos node stores, and, consequently, how much disk\n"
    "space is required. Rolling mode is the smallest and fastest but still sufficient for baking.\n"
    "You can read more about different nodes history modes here:\n"
    "https://tezos.gitlab.io/user/history_modes.html",
    options=history_modes,
    validator=Validator(validators.enum_range(history_modes)),
)

# We define the step as a function to disallow choosing json baking on mainnet
def get_key_mode_query(modes):
    return Step(
        id="key_import_mode",
        prompt="How do you want to import the baker key?",
        help="To register the baker, its secret key needs to be imported to the data "
        "directory first.\nBy default tezos-baking-<network>.service will use the 'baker' "
        "alias\nfor the key that will be used for baking and attesting.\n"
        "If you want to test baking with a faucet file, "
        "make sure you have chosen a test network like " + list(networks.keys())[1],
        options=modes,
        validator=Validator(validators.enum_range(modes)),
    )


ignore_hash_mismatch_options = {
    "no": "Discard the snapshot and return to the previous step",
    "yes": "Continue the setup with this snapshot",
}

ignore_hash_mismatch_query = Step(
    id="ignore_hash_mismatch",
    prompt="Do you want to proceed with this snapshot anyway?",
    help="It's possible, but not recommended, to ignore the sha256 mismatch and use this snapshot anyway.",
    options=ignore_hash_mismatch_options,
    validator=Validator(validators.enum_range(ignore_hash_mismatch_options)),
)


def get_stake_tez_query(staked_balance, minimal_frozen_stake):
    def show_tez(tez):
        # smallest tz quantity is microtez, so we are sure
        # no digits after the 6th after floating point can occur
        if int(tez) == 0:
            return "0"
        elif int(tez) % (10**6) == 0:
            return tez[:-6] + tez[-6:-1].rstrip("0")
        else:
            return tez[:-6] + "." + tez[-6:-1].rstrip("0")

    at_least = int(minimal_frozen_stake) - int(staked_balance)
    return Step(
        id="stake_tez",
        prompt=f"In order to get baking rights, you need to stake at least {show_tez(minimal_frozen_stake)}Tz.\n"
        f"Your current stake amount is {show_tez(staked_balance)}Tz.\n"
        f"You have to stake at least {show_tez(str(at_least))}Tz.\n"
        "How much would you like to stake?",
        help="It is not recommended to stake all the balance, since some funds could require to pay the fees.\n"
        f"For more information, please visit https://tezos.gitlab.io/paris/adaptive_issuance.html#new-staking-mechanism.",
        default=show_tez(str(at_least)),
        validator=Validator([validators.tez_bigger_than(at_least / (10**6))]),
    )


class Setup(Setup):
    # Check if there is already some blockchain data in the octez-node data directory,
    # and ask the user if it can be overwritten.
    def check_blockchain_data(self):
        logging.info("Checking blockchain data")
        node_dir = get_data_dir(self.config["network"])
        node_dir_contents = set()
        try:
            node_dir_contents = set(os.listdir(node_dir))
        except FileNotFoundError:
            print_and_log("The Tezos node data directory does not exist.")
            print_and_log("  Creating directory: " + node_dir)
            proc_call("sudo mkdir " + node_dir)
            proc_call("sudo chown tezos:tezos " + node_dir)

        # Content expected in a configured and clean node data dir
        node_dir_config = set(["config.json", "version.json"])

        # Configure data dir if the config is missing
        if not node_dir_config.issubset(node_dir_contents):
            print_and_log("The Tezos node data directory has not been configured yet.")
            print_and_log("  Configuring directory: " + node_dir)
            network = self.config["network"]
            proc_call(
                "sudo -u tezos octez-node-"
                + self.config["network"]
                + " config init"
                + " --network "
                + network_name_or_teztnets_url(self.config["network"])
                + " --rpc-addr "
                + self.config["node_rpc_addr"]
            )

        diff = node_dir_contents - node_dir_config
        if diff:
            logging.info(
                "The Tezos node data directory already has some blockchain data"
            )
            print("The Tezos node data directory already has some blockchain data:")
            print("\n".join(["- " + os.path.join(node_dir, path) for path in diff]))
            self.query_step(delete_node_data_query)
            if self.config["delete_node_data"] == "yes":
                # We first stop the node service, because it's possible that it
                # will re-create some of the files while we go on with the wizard
                print_and_log("Stopping node service")
                proc_call(
                    "sudo systemctl stop tezos-node-"
                    + self.config["network"]
                    + ".service"
                )
                for path in diff:
                    try:
                        proc_call("sudo rm -r " + os.path.join(node_dir, path))
                    except:
                        logging.error("Could not clean the Tezos node data directory.")
                        print(
                            "Could not clean the Tezos node data directory. "
                            "Please do so manually."
                        )
                        raise OSError(
                            "'sudo rm -r " + os.path.join(node_dir, path) + "' failed."
                        )

                print_and_log("Node directory cleaned.")
                return True
            return False
        return True

    # Check the provider url and collect the most recent snapshot
    # that is suited for the chosen history mode and network
    def get_snapshot_metadata(self, provider: Provider):
        try:
            snapshot_metadata = provider.get_snapshot_metadata(
                self.config["network"],
                self.config["history_mode"],
                self.config["region"],
            )
            if snapshot_metadata is None:
                print_and_log(
                    f"No suitable snapshot found from the {provider.title} provider.",
                    log=logging.warning,
                    colorcode=color_yellow,
                )
            else:
                self.config["snapshots"][provider.title] = snapshot_metadata

        except urllib.error.URLError:
            print_and_log(
                f"\nCouldn't collect snapshot metadata from {provider.metadata_url} due to networking issues.\n",
                log=logging.error,
                colorcode=color_red,
            )
        except ValueError:
            print_and_log(
                f"\nCouldn't collect snapshot metadata from {provider.metadata_url} due to format mismatch.\n",
                log=logging.error,
                colorcode=color_red,
            )
        except Exception as e:
            print_and_log(
                f"\nUnexpected error handling snapshot metadata:\n{e}\n",
                log=logging.error,
            )

    def output_snapshot_metadata(self, name):
        from datetime import datetime
        from locale import setlocale, getlocale, LC_TIME

        # it is portable `C` locale by default
        setlocale(LC_TIME, getlocale())

        metadata = self.config["snapshots"][name]
        timestamp_dt = datetime.strptime(
            metadata["block_timestamp"], "%Y-%m-%dT%H:%M:%SZ"
        )
        timestamp = timestamp_dt.strftime("%c")
        delta = datetime.now() - timestamp_dt
        time_ago = (
            "less than 1 day ago"
            if delta.days == 0
            else "1 day ago"
            if delta.days == 1
            else f"{delta.days} days ago"
        )
        print(
            color(
                f"""
Snapshot metadata:
url: {metadata["url"]}
sha256: {"not provided" if metadata["sha256"] is None else metadata["sha256"]}
filesize: {metadata["filesize"]}
block height: {metadata["block_height"]}
block timestamp: {timestamp} ({time_ago})
""",
                color_green,
            )
        )

    def fetch_snapshot_from_provider(self, name):
        try:
            url = self.config["snapshots"][name]["url"]
            sha256 = self.config["snapshots"][name]["sha256"]
            self.output_snapshot_metadata(name)
            return fetch_snapshot(url, sha256)
        except KeyError:
            raise InterruptStep
        except (ValueError, urllib.error.URLError):
            logging.error(
                "The snapshot snapshot download option user have chosen is unavailable"
            )
            print("The snapshot download option you chose is unavailable,")
            print("which normally shouldn't happen. Please check your")
            print("internet connection or choose another option.")
            print()
            raise InterruptStep

    def get_snapshot_from_provider(self, provider):
        try:
            self.config["snapshots"][provider.title]
        except KeyError:
            self.get_snapshot_metadata(provider)
        snapshot_file = self.fetch_snapshot_from_provider(provider.title)
        snapshot_block_hash = self.config["snapshots"][provider.title]["block_hash"]
        return (snapshot_file, snapshot_block_hash)

    # check if a given provider has the compatible snapshot
    # available in its metadata and return the metadata of this
    # snapshot if it's available
    def try_fallback_provider(self, provider):
        print(f"Getting snapshots' metadata from {provider.title} instead...")
        self.get_snapshot_metadata(provider)
        return self.config["snapshots"].get(provider.title, None)

    # check if some of the providers has the compatible snapshot
    # available in its metadadata and return the provider name
    def find_fallback_provider(self, providers):
        for provider in providers:
            snapshot = self.try_fallback_provider(provider)
            if snapshot is not None:
                return provider
        return None

    # tries to get the latest compatible snapshot from the given
    # provider's metadata
    #
    # if the snapshot not found, tries to find it in other known
    # providers
    def get_snapshot_from_provider_with_fallback(self, provider):
        print_and_log(f"Getting snapshots' metadata from {provider.title}...")

        self.get_snapshot_metadata(provider)
        snapshot = self.config["snapshots"].get(provider.title, None)

        if snapshot is None:
            fallback_providers = default_providers.copy()
            fallback_providers.remove(provider)
            fallback_provider = self.find_fallback_provider(fallback_providers)

            if fallback_provider is None:
                return None
            else:
                provider = fallback_provider

        snapshot_file = self.fetch_snapshot_from_provider(provider.title)
        snapshot_block_hash = self.config["snapshots"][provider.title]["block_hash"]
        return (snapshot_file, snapshot_block_hash)

    def get_snapshot_from_direct_url(self, url):
        try:
            self.query_step(snapshot_sha256_query)
            sha256 = self.config["snapshot_sha256"]
            snapshot_file = fetch_snapshot(url, sha256)
            if sha256:
                print_and_log("Checking the snapshot integrity...")
                check_file_contents_integrity(snapshot_file, sha256)
                print_and_log("Integrity verified.")
            return (snapshot_file, None)
        except (ValueError, urllib.error.URLError):
            print()
            logging.error("The snapshot url provided is unavailable.")
            print("The snapshot URL you provided is unavailable.")
            print("Please check the URL again or choose another option.")
            print()
            raise InterruptStep
        except Sha256Mismatch as e:
            print_and_log("SHA256 mismatch.", logging.error)
            print_and_log(f"Expected sha256: {e.expected_sha256}", logging.error)
            print_and_log(f"Actual sha256: {e.actual_sha256}", logging.error)
            print()
            if self.config["ignore_hash_mismatch"] == "no":
                raise InterruptStep
            else:
                logging.info("Ignoring hash mismatch")
                return (snapshot_file, None)

    def get_snapshot_from_provider_url(self, url):
        provider = XtzShotsLike("custom", url)
        if os.path.basename(provider.metadata_url) == "tezos-snapshots.json":
            return self.get_snapshot_from_provider(provider)
        else:
            try:
                return self.get_snapshot_from_provider(provider)
            except InterruptStep:
                provider.metadata_url = os.path.join(url, "tezos-snapshots.json")
                return self.get_snapshot_from_provider(provider)

    # Importing the snapshot for Node bootstrapping
    def import_snapshot(self):
        do_import = self.check_blockchain_data()
        valid_choice = False

        if do_import:
            self.query_step(history_mode_query)

            logging.info("Updating history mode octez-node config")
            proc_call(
                f"sudo -u tezos octez-node-{self.config['network']} config update "
                f"--history-mode {self.config['history_mode']}"
            )

            self.config["snapshots"] = {}

            os.makedirs(TMP_SNAPSHOT_LOCATION, exist_ok=True)

        else:
            return

        while not valid_choice:

            self.query_step(get_snapshot_mode_query(self.config))

            snapshot_file = TMP_SNAPSHOT_LOCATION
            snapshot_block_hash = None

            try:
                if self.config["snapshot_mode"] == "skip":
                    return
                elif self.config["snapshot_mode"] == "file":
                    self.query_step(snapshot_file_query)
                    snapshot_file = os.path.join(
                        TMP_SNAPSHOT_LOCATION, f"file-{time.time()}.snapshot"
                    )
                    # not copying since it can take a lot of time
                    os.link(self.config["snapshot_file"], snapshot_file)
                elif self.config["snapshot_mode"] == "direct url":
                    self.query_step(snapshot_url_query)
                    url = self.config["snapshot_url"]
                    (
                        snapshot_file,
                        snapshot_block_hash,
                    ) = self.get_snapshot_from_direct_url(url)
                elif self.config["snapshot_mode"] == "provider url":
                    self.query_step(provider_url_query)
                    url = self.config["provider_url"]
                    (
                        snapshot_file,
                        snapshot_block_hash,
                    ) = self.get_snapshot_from_provider_url(url)
                else:
                    for provider in default_providers:
                        if provider.title in self.config["snapshot_mode"]:
                            selected_provider = provider
                    self.config["region"] = None
                    if isinstance(selected_provider, TzInit):
                        self.query_step(region_step)
                    snapshot_info = self.get_snapshot_from_provider_with_fallback(
                        selected_provider
                    )
                    if snapshot_info is None:
                        print_and_log(
                            "Couldn't find available snapshot in any of the known providers.",
                            log=logging.warning,
                            colorcode=color_yellow,
                        )
                        raise InterruptStep
                    (snapshot_file, snapshot_block_hash) = snapshot_info
            except InterruptStep:
                print_and_log("Getting back to the snapshot import mode step.")
                continue

            valid_choice = True

            import_flag = ""
            if is_full_snapshot(snapshot_file, self.config["snapshot_mode"]):
                if self.config["history_mode"] == "archive":
                    import_flag = "--reconstruct "

            block_hash_option = ""
            if snapshot_block_hash is not None:
                block_hash_option = " --block " + snapshot_block_hash

            logging.info("Importing snapshot with the octez-node")
            proc_call(
                "sudo -u tezos octez-node-"
                + self.config["network"]
                + " snapshot import "
                + import_flag
                + snapshot_file
                + block_hash_option
            )

            print_and_log("Snapshot imported.")

            try:
                shutil.rmtree(TMP_SNAPSHOT_LOCATION)
            except:
                pass
            else:
                print_and_log("Deleted the temporary snapshot file.")

    # Bootstrapping octez-node
    def bootstrap_node(self):

        self.import_snapshot()

        logging.info("Starting the node service")
        print(
            "Starting the node service. This is expected to take some "
            "time, as the node needs a node identity to be generated."
        )

        self.systemctl_simple_action("start", "node")

        print_and_log("Waiting for the node service to start...")

        while True:
            rpc_endpoint = self.config["node_rpc_endpoint"]
            try:
                urllib.request.urlopen(rpc_endpoint + "/version")
                break
            except urllib.error.URLError:
                proc_call("sleep 1")

        print_and_log("Generated node identity and started the service.")

        self.systemctl_enable()

        if self.config["mode"] == "node":
            logging.info("The node setup is finished.")
            print(
                "The node setup is finished. It will take some time for the node to bootstrap.",
                "You can check the progress by running the following command:",
            )
            print(f"systemctl status tezos-node-{self.config['network']}.service")

            print()
            print_and_log("Exiting the Tezos Setup Wizard.")
            sys.exit(0)

        print_and_log("Waiting for the node to be bootstrapped...")

        tezos_client_options = self.get_tezos_client_options()
        proc_call(
            f"sudo -u tezos {suppress_warning_text} octez-client {tezos_client_options} bootstrapped"
        )

        print()
        print_and_log("The Tezos node bootstrapped successfully.")

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
                        print(
                            color(
                                "Waiting for your response to the prompt on your Ledger Device...",
                                color_green,
                            )
                        )
                        logging.info("Running octez-client to setup ledger")
                        proc_call(
                            f"sudo -u tezos {suppress_warning_text} octez-client {tezos_client_options} "
                            f"setup ledger to bake for {baker_alias} --main-hwm {self.get_current_head_level()}"
                        )
                        baker_set_up = True
                    except Exception as e:
                        print("Something went wrong when calling octez-client:")
                        print_and_log(str(e), logging.error)
                        print()
                        print("Please check your input and try again.")
                        print_and_log(
                            "Going back to the import mode selection.", logging.error
                        )

                else:
                    baker_set_up = True

    def stake_tez(self):
        def get_minimal_frozen_stake():
            output = get_proc_output(
                f"curl {self.config['node_rpc_endpoint']}/chains/main/blocks/head/context/constants"
            ).stdout.decode("utf-8")
            return json.loads(output)["minimal_frozen_stake"]

        def get_staked_balance(pkh):
            output = get_proc_output(
                f"curl {self.config['node_rpc_endpoint']}/chains/main/blocks/head/context/contracts/{pkh}/staked_balance"
            ).stdout.decode("utf-8")
            return json.loads(output)

        def get_adaptive_issuance_launch_cycle():
            output = get_proc_output(
                f"curl {self.config['node_rpc_endpoint']}/chains/main/blocks/head/context/adaptive_issuance_launch_cycle"
            ).stdout.decode("utf-8")
            return json.loads(output)

        def get_current_cycle():
            output = get_proc_output(
                f"curl {self.config['node_rpc_endpoint']}/chains/main/blocks/head/metadata"
            ).stdout.decode("utf-8")
            return json.loads(output)["level_info"]["cycle"]

        tezos_client_options = self.get_tezos_client_options()
        baker_alias = self.config["baker_alias"]
        baker_key_hash = self.config["baker_key_hash"]

        adaptive_issuance_launch_cycle = get_adaptive_issuance_launch_cycle()

        current_cycle = get_current_cycle()

        # TODO remove this check when ParisB protocol is activated at mainnet
        if adaptive_issuance_launch_cycle is not None and int(current_cycle) >= int(
            adaptive_issuance_launch_cycle
        ):
            minimal_frozen_stake = get_minimal_frozen_stake()

            staked_balance = get_staked_balance(baker_key_hash)

            if int(staked_balance) < int(minimal_frozen_stake):

                self.query_step(
                    get_stake_tez_query(staked_balance, minimal_frozen_stake)
                )

                print_and_log(f"Staking {self.config['stake_tez']}Tz...")

                if self.check_ledger_use():
                    ledger_app = "Wallet"
                    print(f"Please open the Tezos {ledger_app} app on your ledger.")
                    print(
                        color(
                            "Please note, that if you are using Tezos Wallet app of version 3.0.0 or higher,\n"
                            'you need to enable "expert mode" in the Tezos Wallet app settings on the Ledger device.',
                            color_yellow,
                        )
                    )
                    print(
                        color(
                            f"Waiting for the Tezos {ledger_app} to be opened...",
                            color_green,
                        ),
                    )
                    wait_for_ledger_app(ledger_app, self.config["client_data_dir"])
                    print(
                        color(
                            "Waiting for your response to the prompt on your Ledger Device...",
                            color_green,
                        )
                    )

                get_proc_output(
                    f"sudo -u tezos {suppress_warning_text} octez-client {tezos_client_options} "
                    f"stake {self.config['stake_tez']} for {baker_alias}"
                )

                if self.check_ledger_use():
                    ledger_app = "Baking"
                    print(f"Please reopen the Tezos {ledger_app} app on your ledger.")
                    print(
                        color(
                            f"Waiting for the Tezos {ledger_app} to be opened...",
                            color_green,
                        ),
                    )
                    wait_for_ledger_app(ledger_app, self.config["client_data_dir"])

    def register_baker(self):
        print()
        tezos_client_options = self.get_tezos_client_options()
        baker_alias = self.config["baker_alias"]

        if self.check_ledger_use():
            print(
                color(
                    "Waiting for your response to the prompt on your Ledger Device...",
                    color_green,
                )
            )
        proc_call(
            f"sudo -u tezos {suppress_warning_text} octez-client {tezos_client_options} "
            f"register key {baker_alias} as delegate"
        )

    # There is no changing the toggle vote option at a glance,
    # so we need to change the config every time
    def set_liquidity_toggle_vote(self):
        self.query_step(liquidity_toggle_vote_query)

        net = self.config["network"]
        logging.info(
            "Replacing tezos-baking service env with liquidity toggle vote setting"
        )
        replace_systemd_service_env(
            f"tezos-baking-{net}",
            "LIQUIDITY_BAKING_TOGGLE_VOTE",
            f"\"{self.config['liquidity_toggle_vote']}\"",
        )

    def baker_registered(self):
        tezos_client_options = self.get_tezos_client_options()
        baker_alias = self.config["baker_alias"]
        _, baker_key_hash = get_key_address(tezos_client_options, baker_alias)
        try:
            output = get_proc_output(
                f"curl {self.config['node_rpc_endpoint']}/chains/main/blocks/head/context/delegates/{baker_key_hash}"
            ).stdout.decode("utf-8")
            response = json.loads(output)
            return baker_key_hash in response["delegated_contracts"]
        except:
            return False

    def start_baking(self):
        self.systemctl_simple_action("restart", "baking")

    def run_setup(self):

        logging.info("Starting the Tezos Setup Wizard.")

        print(welcome_text)

        self.query_step(network_query)
        self.fill_baking_config()
        self.query_step(service_mode_query)

        print()
        self.query_step(systemd_mode_query)

        print_and_log("Trying to bootstrap octez-node")
        self.bootstrap_node()

        # If we continue execution here, it means we need to set up baking as well.
        executed = False
        while not executed:
            print()
            print_and_log("Importing the baker key")
            self.import_baker_key()

            print()
            try:
                (
                    self.config["baker_key_value"],
                    self.config["baker_key_hash"],
                ) = get_key_address(
                    self.get_tezos_client_options(), self.config["baker_alias"]
                )
                if not self.baker_registered():
                    print_and_log("Registering the baker")
                    self.register_baker()

                self.stake_tez()

                print(
                    "You can check a blockchain explorer (e.g. https://tzkt.io/ or https://tzstats.com/)\n"
                    "to see the baker status and baking rights of your account."
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
                print("Going back to the previous step.")
                print("Please check your input and try again.")
                continue
            executed = True

        self.set_liquidity_toggle_vote()

        print()
        print_and_log("Starting the baking instance")
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
        logging.info("Exiting the Tezos Setup Wizard.")


def main():
    readline.parse_and_bind("tab: complete")
    readline.set_completer_delims(" ")

    try:
        setup_logger("tezos-setup.log")
        setup = Setup()
        setup.run_setup()
    except KeyboardInterrupt as e:
        if "network" in setup.config:
            proc_call(
                "sudo systemctl stop tezos-baking-"
                + setup.config["network"]
                + ".service"
            )
        logging.info(f"Received keyboard interrupt.")
        print_and_log("Exiting the Tezos Setup Wizard.")
        sys.exit(1)
    except EOFError as e:
        if "network" in setup.config:
            proc_call(
                "sudo systemctl stop tezos-baking-"
                + setup.config["network"]
                + ".service"
            )
        logging.info(f"Reached EOF.")
        print_and_log("Exiting the Tezos Setup Wizard.")
        sys.exit(1)
    except Exception as e:
        if "network" in setup.config:
            proc_call(
                "sudo systemctl stop tezos-baking-"
                + setup.config["network"]
                + ".service"
            )

        print_and_log(
            "Error in the Tezos Setup Wizard, exiting.",
            log=logging.error,
            colorcode=color_red,
        )

        log_exception(exception=e, logfile="tezos-setup.log")

        logging.info("Exiting the Tezos Setup Wizard.")
        sys.exit(1)


if __name__ == "__main__":
    main()
