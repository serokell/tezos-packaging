# SPDX-FileCopyrightText: 2023 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

"""
Contains step class definition along with the common steps shared between wizards
"""

from dataclasses import dataclass, field
import textwrap
import sys

from tezos_baking.util import *
from tezos_baking.validators import Validator
import tezos_baking.validators as validators


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
    "ghostnet": "Long running test network, currently using the Oxford Tezos protocol",
    "oxfordnet": "Test network using the Oxford2 Tezos protocol",
    "parisanet": "Test network using the ParisA Tezos protocol",
}

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


replace_key_options = {
    "no": "Keep the existing key",
    "yes": "Import a new key and replace the existing one",
}

replace_key_query = Step(
    id="replace_key",
    prompt="Would you like to import a new key and replace this one?",
    help="It's possible to proceed with the existing baker key, instead of\n"
    "importing new one.",
    options=replace_key_options,
    validator=Validator(validators.enum_range(replace_key_options)),
)
