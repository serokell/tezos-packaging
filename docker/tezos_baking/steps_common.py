#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2022 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

from typing import List, Dict, Callable, Optional, Tuple, Union, Any, Mapping
from dataclasses import dataclass, field
import tezos_baking.validators as validators
import textwrap
from tezos_baking.common import *


@dataclass
class Option:
    item: str
    description: str
    requires: "Step"


@dataclass
class Step:
    id: str
    help: str
    prompt: str
    default: Optional[str] = "1"
    options: Mapping[str, Union[str, Option]] = field(default_factory=lambda: {})
    validator: Union[
        List[Callable[[str], str]],
        Callable[[Dict[str, str]], Callable[[str], str]],
    ] = (lambda x: lambda y: y)
    actions: List[Callable[[str, Dict[str, str]], None]] = field(default_factory=lambda: [])


    def process(self, answer: str, config: Dict[str, str]):
        try:
            answer = self.validate(answer)
        except ValueError as e:
            print(color("Validation error: " + str(e), color_red))
            raise e
        else:
            config[self.id] = answer
            for fill in self.actions:
                fill(answer, config)


    def validate(self, input):
        if isinstance(self.validator, list):
            for v in self.validator:
                input = v(input)
            return input
        else:
            return self.validator(self.options)(input)


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
                prompt = self.options[o] if isinstance(self.options[o], str) else self.options[o].description
                description = textwrap.indent(
                    textwrap.fill(prompt, 60),
                    " " * indent_size,
                ).lstrip()
                if def_i is not None and i == def_i:
                    print(str_format.format(i, o + " (default)", description))
                else:
                    print(str_format.format(i, o, description))
                i += 1
        elif not self.options and self.default is not None:
            print("Default:", self.default)



networks = {
    "mainnet": "Main Tezos network",
    "ghostnet": "Long running test network, currently using the kathmandu Tezos protocol",
    "kathmandunet": "Test network using the kathmandu Tezos protocol",
    "limanet": "Test network using the lima Tezos protocol",
}


key_import_modes = {
    "ledger": "From a ledger",
    "secret-key": "Either the unencrypted or password-encrypted secret key for your address",
    "remote": "Remote key governed by a signer running on a different machine",
    "generate-fresh-key": "Generate fresh key that should be filled manually later",
    "json": "Faucet JSON file",
}


# Steps

secret_key_query = Step(
    id="secret_key",
    prompt="Provide either the unencrypted or password-encrypted secret key for your address.",
    help="The format is 'unencrypted:edsk...' for the unencrypted key, or 'encrypted:edesk...'"
    "for the encrypted key.",
    default=None,
    validator=[validators.required_field, validators.secret_key],
)


def remote_signer_url_action(answer: str, config: Dict[str, str]):
    rsu = re.search(signer_uri_regex.decode(), config["remote_signer_uri"])
    config["remote_host"] = rsu.group(1)
    config["remote_key"] = rsu.group(2)


remote_signer_uri_query = Step(
    id="remote_signer_uri",
    prompt="Provide your remote key with the address of the signer.",
    help="The format is the address of your remote signer host, followed by a public key,\n"
    "i.e. something like http://127.0.0.1:6732/tz1V8fDHpHzN8RrZqiYCHaJM9EocsYZch5Cy\n"
    "The supported schemes are https, http, tcp, and unix.",
    default=None,
    validator=[validators.required_field, validators.signer_uri],
    actions=[remote_signer_url_action],
)

derivation_path_query = Step(
    id="derivation_path",
    prompt="Provide derivation path for the key stored on the ledger.",
    help="The format is '[0-9]+h/[0-9]+h'",
    default=None,
    validator=[validators.required_field, validators.derivation_path],
)


json_filepath_query = Step(
    id="json_filepath",
    prompt="Provide the path to your downloaded faucet JSON file.",
    help="The file should contain the 'mnemonic' and 'secret' fields.",
    default=None,
    validator=[validators.required_field, validators.filepath],
)


def get_ledger_url_query(ledgers):
    return Step(
        id="ledger_url",
        prompt="Choose a ledger to get the new derivation from.",
        options=ledgers,
        default=None,
        validator=[validators.required_field, validators.enum_range(ledgers)],
        help="In order to specify new derivation path, you need to specify a ledger to get the derivation from.",
    )


# We define this step as a function since the corresponding step requires
# tezos-node to be running and bootstrapped in order to gather the data
# about the ledger-stored addresses, so it's called right before invoking
# after the node was boostrapped
def get_ledger_derivation_query(ledgers_derivations, node_endpoint):
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
        options=[ledger_urls_info(ledgers_derivations, node_endpoint)] + extra_options,
        validator=
            [
                validators.required_field,
                validators.enum_range(full_ledger_urls + extra_options),
            ]
        ,
    )
