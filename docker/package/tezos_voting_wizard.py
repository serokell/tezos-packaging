#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2021 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ

"""
A wizard utility to help with voting on the Tezos protocol.

Asks questions, validates answers, and executes the appropriate steps using the final configuration.
"""

import os, sys, subprocess, shlex
import readline
import re, textwrap


# Global options

networks = {
    "mainnet": "Main Tezos network",
    "custom": "Custom network, will require its name",
}

ballot_outcomes = {
    "yay": "Vote for accepting the proposal",
    "nay": "Vote for rejecting the proposal",
    "pass": "Submit a vote not influencing the result but contributing to quorum",
}

# Regexes

ledger_regex = b"ledger:\/\/[\w\-]+\/[\w\-]+\/[\w']+\/[\w']+"
protocol_hash_regex = (
    b"P[123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz]{50}"
)

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


def required_field_validator(input):
    if not input.strip():
        raise ValueError("Please provide this required option.")
    return input


# To be validated, the input should adhere to the protocol hash format:
# <base58 encoded string with length 51 starting with P>
def protocol_hash_validator(input):
    proto_hash_regex_str = protocol_hash_regex.decode("utf-8")
    match = re.match(proto_hash_regex_str, input.strip())
    if not bool(match):
        raise ValueError(
            "The input doesn't match the format for the protocol hash: "
            + proto_hash_regex_str
            + "\nPlease check the input and try again."
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

welcome_text = """Tezos Voting Wizard

Welcome, this wizard will help you to vote in the Tezos protocol amendment process.
Please note that for this you need to already have set up the baking infrastructure,
normally on mainnet, as only bakers can submit ballots or proposals.

If you have installed tezos-baking, you can run Tezos Setup Wizard to set it up:
tezos-setup-wizard

Alternatively, you can use this wizard for voting on a custom chain,
which also needs to be set up already.

All commands within the service are run under the 'tezos' user.

To access help and possible options for each question, type in 'help' or '?'.
Type in 'exit' to quit.
"""

suppress_warning_text = "TEZOS_CLIENT_UNSAFE_DISABLE_DISCLAIMER=YES"


def proc_call(cmd):
    return subprocess.check_call(shlex.split(cmd))


def get_proc_output(cmd):
    if sys.version_info.major == 3 and sys.version_info.minor < 7:
        return subprocess.run(shlex.split(cmd), stdout=subprocess.PIPE)
    else:
        return subprocess.run(shlex.split(cmd), capture_output=True)


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


# we don't need any data here, just a confirmation Tezos Wallet app is open
def wait_for_ledger_wallet_app():
    output = b""
    while re.search(b"Found a Tezos Wallet", output) is None:
        output = get_proc_output(
            f"sudo -u tezos {suppress_warning_text} tezos-client list connected ledgers"
        ).stdout
        proc_call("sleep 1")


def search_baking_service_config(config_contents, regex, default):
    res = re.search(regex, config_contents)
    if res is None:
        return default
    else:
        return res.group(1)


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
    id="network_mode",
    prompt="Which Tezos network would you like to use?\n",
    help="The selected network will be used for voting.\n"
    "Usually you would vote on the mainnet, but you can also select\n"
    "a custom network (needs to already be set up).",
    options=networks,
    validator=Validator(enum_range_validator(networks)),
)

custom_network_query = Step(
    id="custom_network_name",
    prompt="What's the name of the custom network you'd like to use?",
    help="The selected network will be used to vote.\n"
    "For example, to use the tezos-baking-custom@voting service, input 'voting'."
    "You need to already have set up the custom network using systemd services.",
    # TODO: "\nYou can follow a tutorial here:",
    validator=Validator(required_field_validator),
)

new_proposal_query = Step(
    id="new_proposal_hash",
    prompt="Provide the hash for your newly submitted proposal.",
    default=None,
    help="The format is 'P[123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz]{50}'",
    validator=Validator([required_field_validator, protocol_hash_validator]),
)

# We define this step as a function since the corresponding step requires that we get the
# proposal hashes off the chain.
# tezos-client supports submitting up to 20 proposal hashes at a time, but it seems like this
# isn't recommended for use with Ledger, so we leave it at one hash pro query for now.
def get_proposal_period_hash(hashes):

    # if the chain is in the proposal period, it's possible to submit a new proposal hash
    extra_options = ["Specify new proposal hash"]

    return Step(
        id="chosen_hash",
        prompt="Select a proposal hash.\n"
        "You can choose one of the suggested hashes or provide your own:",
        help="You can submit one proposal at a time.\n"
        "'Specify new proposal hash' will ask a protocol hash from you. ",
        default=None,
        options=hashes + extra_options,
        validator=Validator(
            [
                required_field_validator,
                enum_range_validator(hashes + extra_options),
            ]
        ),
    )


ballot_outcome_query = Step(
    id="ballot_outcome",
    prompt="Choose the outcome for your ballot.",
    help="'yay' is for supporting the proposal, 'nay' is for rejecting the proposal,\n"
    "'pass' is used to not influence a vote but still contribute to reaching a quorum.",
    default=None,
    options=ballot_outcomes,
    validator=Validator(
        [required_field_validator, enum_range_validator(ballot_outcomes)]
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

    # Check whether the baker_alias account is set up to use ledger
    def check_ledger_use(self):
        baker_alias = self.config["baker_alias"]
        address = get_proc_output(
            f"sudo -u tezos {suppress_warning_text} tezos-client "
            f"{self.config['tezos_client_options']} show address {baker_alias} --show-secret"
        )
        if address.returncode == 0:
            value_regex = b"(?:" + ledger_regex + b")"
            return bool(re.match(value_regex, address.stdout))

    def check_baking_service(self):
        net = self.config["network_suffix"]
        try:
            proc_call(f"systemctl is-active --quiet tezos-baking-{net}.service")
        except:
            print(f"Looks like the tezos-baking-{net} service isn't running.")
            print("Please start the service or set up baking.")
            if self.config["network_mode"] == "mainnet":
                print("You can do this by running:")
                print("tezos-setup-wizard")
            sys.exit(1)

    def check_data_correctness(self):
        print("Baker data detected is as follows:")
        print(f"Data directory: {self.config['client_data_dir']}")
        print(f"Node RPC address: {self.config['node_rpc_addr']}")
        print(f"Baker alias: {self.config['baker_alias']}")
        if not yes_or_no("Does this look correct? (Y/n)", "yes"):
            print("Try setting up baking again by running:")
            print("tezos-setup-wizard")
            sys.exit(1)

    def get_network(self):
        self.query_step(network_query)

        if self.config["network_mode"] == "mainnet":
            self.config["network_suffix"] = "mainnet"
        elif self.config["network_mode"] == "custom":
            # TODO: maybe check/validate this
            self.query_step(custom_network_query)
            self.config["network_suffix"] = (
                "custom@" + self.config["custom_network_name"]
            )

    def fill_baking_config(self):
        net = self.config["network_suffix"]
        output = get_proc_output(f"systemctl show tezos-baking-{net}.service").stdout
        config_filepath = re.search(b"EnvironmentFiles=(.*) ", output)
        if config_filepath is None:
            print(
                f"EnvironmentFiles not found in tezos-baking-{net}.service configuration,",
                f"defaulting to /etc/default/tezos-baking-{net}",
            )
            config_filepath = f"/etc/default/tezos-baking-{net}"
        else:
            config_filepath = config_filepath.group(1).decode().strip()

        with open(config_filepath, "r") as f:
            config_contents = f.read()
            self.config["client_data_dir"] = search_baking_service_config(
                config_contents, 'DATA_DIR="(.*)"', "/var/lib/tezos/.tezos-client"
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

    def fill_voting_period_info(self):
        voting_proc = get_proc_output(
            f"sudo -u tezos {suppress_warning_text} tezos-client "
            f"{self.config['tezos_client_options']} show voting period"
        )
        if voting_proc.returncode == 0:
            info = voting_proc.stdout
        else:
            print(
                "Couldn't get the voting period info. Please check that the network",
                "for voting has been set up correctly.",
            )

        self.config["amendment_phase"] = (
            re.search(b'Current period: "(\w+)"', info).group(1).decode("utf-8")
        )
        self.config["proposal_hashes"] = [
            phash.decode() for phash in re.findall(protocol_hash_regex, info)
        ]

    def process_proposal_period(self):
        self.query_step(get_proposal_period_hash(self.config["proposal_hashes"]))

        hash_to_submit = self.config["chosen_hash"]
        if hash_to_submit == "Specify new proposal hash":
            self.query_step(new_proposal_query)
            hash_to_submit = self.config["new_proposal_hash"]

        result = get_proc_output(
            f"sudo -u tezos {suppress_warning_text} tezos-client {self.config['tezos_client_options']} "
            f"submit proposals for {self.config['baker_alias']} {hash_to_submit}"
        )

        if result.returncode == 0:
            if yes_or_no("Submission successful! Choose again? <Y/n> ", "yes"):
                self.process_proposal_period()
                return
        else:
            print()

            if re.search(b"[Ii]nvalid proposal", result.stderr) is not None:
                print(color("The submitted proposal hash is invalid.", color_red))
                print("Check your custom submitted proposal hash and try again.")
                self.process_proposal_period()
                return
            elif re.search(b"Unauthorized proposal", result.stderr) is not None:
                print(
                    color(
                        "Cannot submit because of an unauthorized proposal.", color_red
                    )
                )
                print("This means you are not present in the voting listings.")
            elif re.search(b"Not in a proposal period", result.stderr) is not None:
                print(
                    color(
                        "Cannot submit because the voting period is no longer 'proposal'.",
                        color_red,
                    )
                )
                print("This means the voting period has already advanced.")
            elif re.search(b"Too many proposals", result.stderr) is not None:
                print(
                    color(
                        "Cannot submit because of too many proposals submitted.",
                        color_red,
                    )
                )
                print("This means you have already submitted more than 20 proposals.")
            # No other "legitimate" proposal error ('empty_proposal', 'unexpected_proposal')
            # should be possible with the wizard, so we just raise an error with the whole output.
            else:
                print(
                    "Something went wrong when calling tezos-client. Please consult the logs."
                )
                raise OSError(result.stderr.decode())

            print("Please check your baker data and possibly try again.")

    def process_voting_period(self):
        print("The current proposal is:")
        # there's only one in any voting (exploration/promotion) period
        print(self.config["proposal_hashes"][0])
        print()

        self.query_step(ballot_outcome_query)

        result = get_proc_output(
            f"sudo -u tezos {suppress_warning_text} tezos-client {self.config['tezos_client_options']} "
            f"submit ballot for {self.config['baker_alias']} {self.config['proposal_hashes'][0]} "
            f"{self.config['ballot_outcome']}"
        )

        if result.returncode != 0:
            # handle the 'unauthorized ballot' error
            # Unfortunately, despite the error's description text, tezos-client seems to use this error
            # both when the baker has already voted and when the baker was not in the voting listings
            # in the first place, so it's difficult to distinguish between the two cases.
            if re.search(b"Unauthorized ballot", result.stderr) is not None:
                print()
                print(
                    color("Cannot vote because of an unauthorized ballot.", color_red)
                )
                print(
                    "This either means you have already voted or that you are not in the",
                    "voting listings in the first place.",
                )
                print("Please check your baker data and possibly try again.")
            if (
                re.search(b"Not in Exploration or Promotion period", result.stderr)
                is not None
            ):
                print()
                print(
                    color("Cannot vote because the voting period is", color_red),
                    color(f"no longer '{self.config['amendment_phase']}'.", color_red),
                )
                print(
                    "This most likely means the voting period has already advanced to the next one.",
                )
            # No other "legitimate" voting error ('invalid_proposal', 'unexpected_ballot')
            # should be possible with the wizard, so we just raise an error with the whole output.
            else:
                print(
                    "Something went wrong when calling tezos-client. Please consult the logs."
                )
                raise OSError(result.stderr.decode())

    def run_voting(self):

        print(welcome_text)

        self.get_network()

        self.fill_baking_config()

        self.check_baking_service()

        # check with the user that the baker data sounds correct
        self.check_data_correctness()

        self.config["tezos_client_options"] = self.get_tezos_client_options()

        # if a ledger is used for baking, ask to open Tezos Wallet app on it before proceeding
        if self.check_ledger_use():
            print()
            print("Please open the Tezos Wallet app on your ledger.")
            wait_for_ledger_wallet_app()

        # process 'tezos-client show voting period'
        self.fill_voting_period_info()

        print(
            f"The amendment is currently in the {self.config['amendment_phase']} period."
        )
        if self.config["amendment_phase"] == "proposal":
            print(
                "Bakers can submit up to 20 protocol amendment proposals,",
                "including supporting existing ones.",
            )
            print()
            self.process_proposal_period()
        elif self.config["amendment_phase"] in ["exploration", "promotion"]:
            print(
                "Bakers can submit one ballot regarding the current proposal,",
                "voting either 'yay', 'nay', or 'pass'.",
            )
            print()
            self.process_voting_period()
        else:
            print("Voting isn't possible at the moment.")
            print("Exiting the Tezos Voting Wizard.")

        print()
        print("Thank you for voting!")


if __name__ == "__main__":
    readline.parse_and_bind("tab: complete")
    readline.set_completer_delims(" ")

    try:
        setup = Setup()
        setup.run_voting()
    except KeyboardInterrupt:
        print("Exiting the Tezos Voting Wizard.")
        sys.exit(1)
    except EOFError:
        print("Exiting the Tezos Voting Wizard.")
        sys.exit(1)
    except Exception as e:
        print("Error in Tezos Voting Wizard, exiting.")
        logfile = "tezos_voting_wizard.log"
        with open(logfile, "a") as f:
            f.write(str(e) + "\n")
        print("The error has been logged to", os.path.abspath(logfile))
        sys.exit(1)
