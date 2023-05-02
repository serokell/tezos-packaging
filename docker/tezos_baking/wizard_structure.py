# SPDX-FileCopyrightText: 2023 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

"""
Contains shared code from all Tezos wizards for a command line wizard skeleton.

Helps with writing a tool that asks questions, validates answers, and executes
the appropriate steps using the final configuration.
"""

import os, sys, subprocess, shlex, shutil
import re
import urllib.request
import json
from typing import List, Dict, Callable, Optional, Tuple, Union, Any
from dataclasses import dataclass, field
import tezos_baking.steps_common as steps
from tezos_baking.steps_common import Step, get_systemd_service_env, networks, key_import_modes, get_replace_baker_key_query
from tezos_baking.common import *


def get_step_path(args, step: Step) -> List[Tuple[str, Step]]:
    argument: Optional[str] = getattr(args, step.id, None)
    if argument is None:
        paths = []
        for (k, v) in step.options.items():
            if isinstance(v, str):
                continue
            path = get_step_path(args, v.requires)
            if path:
                paths.append((v.item, path))
        if len(paths) > 1:
            raise ValueError(f"Conflicting arguments: {', '.join(path[1][-1][1].id for path in paths)}")
        elif len(paths) == 1:
            (answer, path) = paths[0]
            return [(answer, step)] + path
        else:
            return []
    else:
        return [(argument, step)]


class Setup:
    def __init__(self, config={}, args=None):
        self.config = config
        self.args = args


    def ensure_step(self, step: Step):
        if self.config.get(step.id, None) is None:
            self.query_step(step)


    def query_step(self, step: Step):
        def interactive_query():
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
                        step.process(answer, self.config)
                    except ValueError:
                        continue
                    else:
                        validated = True

        steps_to_fill = get_step_path(self.args, step)
        if steps_to_fill:
            for (answer, step) in steps_to_fill:
                step.process(answer, self.config)
        else:
            if self.args.non_interactive:
                if step.default is not None:
                    step.process(step.default, self.config)
                else:
                    print(f"Validation error: argument {step.id} is not supplied.", color_red)
                    raise ValueError(f"Missing argument: {step.id}")
            else:
                interactive_query()



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
        proc_call(
            f"sudo -u tezos {suppress_warning_text} octez-client "
            f"{self.config['tezos_client_options']} config update"
        )

    def get_current_head_level(self):
        response = urllib.request.urlopen(
            self.config["node_rpc_endpoint"] + "/chains/main/blocks/head/header"
        )
        return str(json.load(response)["level"])

    # Check if an account with the baker_alias alias already exists, and ask the user
    # if it can be overwritten.
    def check_baker_account(self):
        baker_alias = self.config["baker_alias"]
        baker_key_value = get_key_address(self.get_tezos_client_options(), baker_alias)
        if baker_key_value is not None:
            self.ensure_step(get_replace_baker_key_query(self.config, baker_key_value))
            return self.config["replace_baker_key"] == "yes"
        else:
            return True

    def import_key(self, key_mode_query, ledger_app=None):

        baker_alias = self.config["baker_alias"]
        tezos_client_options = self.get_tezos_client_options()

        valid_choice = False
        while not valid_choice:

            self.ensure_step(key_mode_query)

            try:
                if self.config["key_import_mode"] == "secret-key":
                    self.ensure_step(steps.secret_key_query)
                    proc_call(
                        f"sudo -u tezos {suppress_warning_text} octez-client {tezos_client_options} "
                        f"import secret key {baker_alias} {self.config['secret_key']} --force"
                    )
                elif self.config["key_import_mode"] == "remote":
                    self.query_step(steps.remote_signer_uri_query)

                    tezos_client_options = self.get_tezos_client_options()
                    proc_call(
                        f"sudo -u tezos {suppress_warning_text} octez-client {tezos_client_options} "
                        f"import secret key {baker_alias} remote:{self.config['remote_key']} --force"
                    )
                elif self.config["key_import_mode"] == "generate-fresh-key":
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
                    print(
                        f"Before proceeding with baker registration you'll need to provide this address with some XTZ.\n"
                        f"Note that you need at least 6000 XTZ in order to receive baking and endorsing rights.\n"
                        f"You can do fill your address using faucet: https://faucet.{network}.teztnets.xyz/.\n"
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
                        print("Going back to the import mode selection.")
                        continue
                elif self.config["key_import_mode"] == "json":
                    self.ensure_step(steps.json_filepath_query)
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
                    ledgers_derivations = wait_for_ledger_app(
                        ledger_app,
                        self.config["client_data_dir"],
                    )
                    if ledgers_derivations is None:
                        print("Going back to the import mode selection.")
                        continue
                    ledgers = list(ledgers_derivations.keys())
                    baker_ledger_url = ""
                    while re.match(ledger_regex.decode(), baker_ledger_url) is None:
                        self.ensure_step(
                            steps.get_ledger_derivation_query(
                                ledgers_derivations,
                                self.config["node_rpc_endpoint"],
                                self.config["client_data_dir"],
                            )
                        )
                        if self.config["ledger_derivation"] == "Go back":
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
                                    self.ensure_step(steps.get_ledger_url_query(ledgers))
                                    ledger_url = self.config["ledger_url"]
                                self.ensure_step(steps.derivation_path_query)
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
                    proc_call(
                        f"sudo -u tezos {suppress_warning_text} octez-client {tezos_client_options} "
                        f"import secret key {baker_alias} {baker_ledger_url} --force"
                    )

            except EOFError:
                raise EOFError
            except Exception as e:
                print("Something went wrong when calling octez-client:")
                print(str(e))
                print()
                print("Please check your input and try again.")
            else:
                valid_choice = True
                value, _ = get_key_address(
                    tezos_client_options, self.config["baker_alias"]
                )
                self.config["baker_key_value"] = value
