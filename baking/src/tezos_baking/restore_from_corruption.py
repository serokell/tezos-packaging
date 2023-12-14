# SPDX-FileCopyrightText: 2023 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

import os
import urllib
import json
import shutil

from tezos_baking.util import extract_relevant_snapshot, fetch_snapshot, get_proc_output
from tezos_baking.tezos_setup_wizard import default_providers


def check_node_corruption():
    network = os.environ.get("NETWORK", None)
    if not network:
        print(
            """
            Could not find network name in environment.
            Can't check node for corruption
        """
        )
        return False
    logs = get_proc_output(f"journalctl -u tezos-node-{network}.service")
    if b"Inconsistent_store" in logs.stdout:
        return True
    return False


def restore_from_corruption():
    history_mode = None
    with open(f"{os.environ['TEZOS_NODE_DIR']}/config.json") as f:
        history_mode = json.load(f)["shell"]["history_mode"]

    node_data_directory = os.environ["TEZOS_NODE_DIR"]
    try:
        shutil.rmtree(node_data_directory)
    except Exception as e:
        print("Could not delete node data dir. Manual restoration is required")

    snapshot_array = None
    config = {"network": os.environ["NETWORK"], "history_mode": history_mode}

    snapshot_array = None
    for json_url in default_providers.values():
        with urllib.request.urlopen(json_url) as url:
            snapshot_array = json.load(url)["data"]
        if snapshot_array is not None:
            break

    snapshot_array.sort(reverse=True, key=lambda x: x["block_height"])

    snapshot_meta = extract_relevant_snapshot(snapshot_array, config)

    snapshot_path = fetch_snapshot(snapshot_meta["url"])

    reinstallation_result = get_proc_output(
        f"""
        octez-node snapshot import {snapshot_path}
    """
    )

    os.remove(snapshot_path)

    if not reinstallation_result.returncode:
        print("Recovery from corruption was successfull")
    else:
        print("Recovery from corruption failed. Manual restoration is required")


def main():
    is_corrupted = check_node_corruption()
    is_baking_installed = (
        b"tezos-baking" in get_proc_output("which octez-baking").stdout
    )
    should_restore = os.environ["RESTORE_FROM_CORRUPTION"]
    if not is_corrupted:
        print(
            """
            Node is not corrupted.
        """
        )
        return
    if not is_baking_installed:
        print(
            """
                Node has been corrupted.
                It order to restore it, you need `octez-baking` to be installed
            """
        )
        return
    if not should_restore:
        print(
            """
                Node has been corrupted.
                Automatic restoration is disabled.
                Manual restoration is required.
            """
        )
        return
    restore_from_corruption()


if __name__ == "__main__":
    main()
