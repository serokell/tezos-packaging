# SPDX-FileCopyrightText: 2022 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

"""
Contains shared code from all Tezos wizards for a command line wizard skeleton.

Helps with writing a tool that asks questions, validates answers, and executes
the appropriate steps using the final configuration.
"""

import os, sys, subprocess, shlex
import re, textwrap
import argparse

# Regexes

secret_key_regex = b"(encrypted|unencrypted):(?:\w{54}|\w{88})"
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


# To be validated, the input should adhere to the derivation path format:
# [0-9]+h/[0-9]+h
def derivation_path_validator(input):
    match = re.match(b"[0-9]+h\/[0-9]+h".decode("utf-8"), input.strip())
    if not bool(match):
        raise ValueError(
            "The input doesn't match the format for the derivation path: "
            "'[0-9]+h/[0-9]+h'"
            "\nPlease check the input and try again."
        )
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


# Command line argument parsing


parser = argparse.ArgumentParser()


# Utilities


def proc_call(cmd):
    return subprocess.check_call(shlex.split(cmd))


def get_proc_output(cmd):
    if sys.version_info.major == 3 and sys.version_info.minor < 7:
        return subprocess.run(shlex.split(cmd), stdout=subprocess.PIPE)
    else:
        return subprocess.run(shlex.split(cmd), capture_output=True)


def progressbar_hook(chunk_number, chunk_size, total_size):
    done = chunk_number * chunk_size
    percent = min(int(done * 100 / total_size), 100)
    print("Progress:", percent, "%,", int(done / (1024 * 1024)), "MB", end="\r")


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


# Wizard CLI skeleton


suppress_warning_text = "TEZOS_CLIENT_UNSAFE_DISABLE_DISCLAIMER=YES"


def get_data_dir(network):
    output = get_proc_output("systemctl show tezos-node-" + network + ".service").stdout
    config = re.search(b"Environment=(.*)(?:$|\n)", output)
    if config is None:
        print(
            "tezos-node-" + network + ".service configuration not found, "
            "defaulting to /var/lib/tezos/node-" + network
        )
        return "/var/lib/tezos/node-" + network
    config = config.group(1)
    data_dir = re.search(b"DATA_DIR=(.*?)(?: |$|\n)", config)
    if data_dir is not None:
        return data_dir.group(1).decode("utf-8")
    else:
        print("DATA_DIR is undefined, defaulting to /var/lib/tezos/node-" + network)
        return "/var/lib/tezos/node-" + network


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
            str_format = f"{{:{index_len}}}. {{:<26}}  {{}}"
            for o in self.options:
                description = textwrap.indent(
                    textwrap.fill(self.options[o], 60), " " * 31
                ).lstrip()
                if def_i is not None and i == def_i:
                    print(str_format.format(i, o + " (default)", description))
                else:
                    print(str_format.format(i, o, description))
                i += 1


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

    def systemctl_start_action(self, service):
        proc_call(
            f"sudo systemctl start tezos-{service}-{self.config['network']}.service"
        )

    def systemctl_enable(self):
        if self.config["systemd_mode"] == "yes":
            print(
                "Enabling the tezos-{}-{}.service".format(
                    self.config["mode"], self.config["network"]
                )
            )
            proc_call(
                f"sudo systemctl enable tezos-{self.config['mode']}-"
                f"{self.config['network']}.service"
            )
        else:
            print("The services won't restart on boot.")

    def get_tezos_client_options(self):
        return (
            "--base-dir "
            + self.config["client_data_dir"]
            + " --endpoint "
            + self.config["node_rpc_addr"]
        )

    def fill_baking_config(self):
        net = self.config["network"]
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
