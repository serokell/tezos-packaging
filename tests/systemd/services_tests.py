# SPDX-FileCopyrightText: 2022 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

from pystemd.systemd1 import Unit
from subprocess import CalledProcessError
from time import sleep
from typing import List

from tezos_baking.wizard_structure import (
    get_key_address,
    proc_call,
    replace_systemd_service_env,
    url_is_reachable,
)

import contextlib
import os.path


@contextlib.contextmanager
def unit(service_name: str):
    unit = Unit(service_name.encode(), _autoload=True)
    unit.Unit.Start("replace")
    while unit.Unit.ActiveState == b"activating":
        sleep(1)
    try:
        yield unit
    finally:
        unit.Unit.Stop("replace")
        while unit.Unit.ActiveState not in [b"failed", b"inactive"]:
            sleep(1)


@contextlib.contextmanager
def account(alias: str):
    # Generate baker key
    proc_call(f"sudo -u tezos octez-client gen keys {alias} --force")
    try:
        yield alias
    finally:
        proc_call(f"sudo -u tezos octez-client forget address {alias} --force")


def retry(action, name: str, retry_count: int = 20) -> bool:
    if action(name):
        return True
    elif retry_count == 0:
        return False
    else:
        sleep(5)
        return retry(action, name, retry_count - 1)


def check_running_process(process_name: str) -> bool:
    def check_process(process_name):
        try:
            proc_call(f"pgrep -f {process_name}")
            return True
        except CalledProcessError:
            return False

    return retry(check_process, process_name)


def check_active_service(service_name: str) -> bool:
    def check_service(service_name):
        try:
            proc_call(f"systemctl is-active --quiet {service_name}")
            return True
        except CalledProcessError:
            return False

    return retry(check_service, service_name)


def generate_identity(network):
    if not os.path.exists(f"/var/lib/tezos/{network}/identity.json"):
        proc_call(
            f"sudo -u tezos octez-node identity generate 1 --data-dir /var/lib/tezos/{network}"
        )


def node_service_test(network: str, rpc_endpoint="http://127.0.0.1:8732"):
    generate_identity(network)
    with unit(f"tezos-node-{network}.service") as _:
        # checking that service started 'tezos-node' process
        assert check_running_process("octez-node")
        # checking that node is able to respond on RPC requests
        assert retry(url_is_reachable, f"{rpc_endpoint}/chains/main/blocks/head")


def baking_service_test(network: str, protocols: List[str], baker_alias="baker"):
    with account(baker_alias) as _:
        generate_identity(network)
        with unit(f"tezos-baking-{network}.service") as _:
            assert check_active_service(f"tezos-node-{network}.service")
            assert check_running_process("octez-node")
            for protocol in protocols:
                assert check_active_service(
                    f"tezos-baker-{protocol.lower()}@{network}.service"
                )
                assert check_running_process(f"octez-baker-{protocol}")


signer_unix_socket = '"/tmp/signer-socket"'

signer_backends = {
    "http": "http://localhost:8080/",
    "tcp": "tcp://localhost:8000/",
    "unix": f"unix:{signer_unix_socket}?pkh=",
}


def signer_service_test(service_type: str):
    with unit(f"tezos-signer-{service_type}.service") as _:
        assert check_running_process(f"octez-signer")
        proc_call(
            "sudo -u tezos octez-signer -d /var/lib/tezos/signer gen keys remote --force"
        )
        remote_key = get_key_address("-d /var/lib/tezos/signer", "remote")[1]
        proc_call(
            f"octez-client import secret key remote-signer {signer_backends[service_type]}{remote_key} --force"
        )
        proc_call("octez-client --mode mockup sign bytes 0x1234 for remote-signer")


def test_node_mainnet_service():
    node_service_test("mainnet")


def test_node_mumbainet_service():
    node_service_test("mumbainet")


def test_baking_mumbainet_service():
    baking_service_test("mumbainet", ["PtMumbai"])


def test_baking_mainnet_service():
    baking_service_test("mainnet", ["PtMumbai"])


def test_http_signer_service():
    signer_service_test("http")


def test_tcp_signer_service():
    signer_service_test("tcp")


def test_standalone_accuser_service():
    with unit(f"tezos-node-mumbainet.service") as _:
        with unit(f"tezos-accuser-ptmumbai.service") as _:
            assert check_running_process(f"octez-accuser-PtMumbai")


def test_unix_signer_service():
    replace_systemd_service_env("tezos-signer-unix", "SOCKET", signer_unix_socket)
    signer_service_test("unix")


def test_standalone_baker_service():
    replace_systemd_service_env(
        "tezos-baker-ptmumbai",
        "TEZOS_NODE_DIR",
        "/var/lib/tezos/node-mumbainet",
    )
    with account("baker") as _:
        with unit(f"tezos-node-mumbainet.service") as _:
            with unit(f"tezos-baker-ptmumbai.service") as _:
                assert check_active_service(f"tezos-baker-ptmumbai.service")
                assert check_running_process(f"octez-baker-PtMumbai")


def test_nondefault_node_rpc_endpoint():
    rpc_addr = "127.0.0.1:8735"
    replace_systemd_service_env("tezos-node-mumbainet", "NODE_RPC_ADDR", rpc_addr)
    proc_call("cat /etc/default/tezos-node-mumbainet")
    try:
        node_service_test("mumbainet", f"http://{rpc_addr}")
    finally:
        replace_systemd_service_env(
            "tezos-node-mumbainet", "NODE_RPC_ADDR", "127.0.0.1:8732"
        )


def test_nondefault_baking_config():
    replace_systemd_service_env(
        "tezos-baking-mumbainet", "BAKER_ADDRESS_ALIAS", "another_baker"
    )
    replace_systemd_service_env(
        "tezos-baking-mumbainet", "LIQUIDITY_BAKING_TOGGLE_VOTE", "on"
    )
    baking_service_test("mumbainet", ["PtMumbai"], "another_baker")
