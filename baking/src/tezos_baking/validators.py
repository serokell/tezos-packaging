# SPDX-FileCopyrightText: 2023 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

"""
Contains user input validators
"""

import re
import os

from .util import *


def enum_range(options):
    def _validator(input):
        intrange = list(map(str, range(1, len(options) + 1)))
        if input not in intrange and input not in options:
            raise ValueError(
                "Please choose one of the provided values or use their respective numbers."
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


def dirpath(input):
    if input and not os.path.isdir(input):
        raise ValueError("Please input a valid path to a directory.")
    return input


def filepath(input):
    if input and not os.path.isfile(os.path.expanduser(input)):
        raise ValueError("Please input a valid file path.")
    return os.path.expanduser(input)


def reachable_url(suffix=None):
    def _validator(input):
        full_url = mk_full_url(input, suffix)
        if url_is_reachable(full_url):
            return full_url
        else:
            raise ValueError(f"{full_url} is unreachable. Please input a valid URL.")

    return _validator


def required_field(input):
    if not input.strip():
        raise ValueError("Please provide this required option.")
    return input


# The input has to be valid to at least one of the two passed validators.
def any_of(validator1, validator2):
    def _validator(input):
        try:
            return validator1(input)
        except:
            return validator2(input)

    return _validator


# Runs the input through the passed validator, allowing for possible alteration,
# but doesn't raise an exception if it doesn't validate to allow for custom options, too.
def or_custom(validator):
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
def secret_key(input):
    match = re.match(secret_key_regex.decode("utf-8"), input.strip())
    if not bool(match):
        raise ValueError(
            "The input doesn't match the format for a Tezos secret key: "
            "{{encrypted, unencrypted}:<base58 encoded string with length 54 or 88>}"
            "\nPlease check the input and try again."
        )
    return input


# To be validated, the input should adhere to the Tezos secret key format:
# {encrypted, unencrypted}:<base58 encoded string with length 54 or 88>
def unencrypted_secret_key(input):
    match = re.match(unencrypted_secret_key_regex.decode("utf-8"), input.strip())
    if not bool(match):
        raise ValueError(
            "The input doesn't match the format for a Tezos secret key: "
            "{{encrypted, unencrypted}:<base58 encoded string with length 54 or 88>}"
            "\nPlease check the input and try again."
        )
    return input


# To be validated, the input should adhere to the derivation path format:
# [0-9]+h/[0-9]+h
def derivation_path(input):
    derivation_path_regex_str = "[0-9]+h\/[0-9]+h"
    match = re.match(derivation_path_regex_str, input.strip())
    if not bool(match):
        raise ValueError(
            "The input doesn't match the format for a derivation path: "
            + derivation_path_regex_str
            + "\nPlease check the input and try again."
        )
    return input


# To be validated, the input should adhere to the signer URI format:
# (tcp|unix|https|http)://<host address>/tz[123]\w{33}
def signer_uri(input):
    match = re.match(signer_uri_regex.decode("utf-8"), input.strip())
    if not bool(match):
        raise ValueError(
            "The input doesn't match the format for a remote signer URI: "
            + "(tcp|unix|https|http)://<host address>/<public key address>"
            + "\nPlease check the input and try again."
        )
    return input


# To be validated, the input should adhere to the protocol hash format:
# <base58 encoded string with length 51 starting with P>
def protocol_hash(input):
    proto_hash_regex_str = protocol_hash_regex.decode("utf-8")
    match = re.match(proto_hash_regex_str, input.strip())
    if not bool(match):
        raise ValueError(
            "The input doesn't match the format for a protocol hash: "
            + proto_hash_regex_str
            + "\nPlease check the input and try again."
        )
    return input


from dataclasses import dataclass
from typing import *

ValidatorFunction = Callable[[str], str]


@dataclass
class Validator:
    validator: Union[
        ValidatorFunction,
        List[ValidatorFunction],
    ] = lambda x: x

    def validate(self, input: str):
        if isinstance(self.validator, list):
            for v in self.validator:
                input = v(input)
            return input
        else:
            return self.validator(input)
