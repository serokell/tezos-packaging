# SPDX-FileCopyrightText: 2020 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ

# This script is used in tezos-binaries.nix and isn't supposed to be run
# other way than 'nix-build tezos-binaries.nix'
machine.succeed('export TEZOS_LOG="* -> warning"')
machine.succeed("mkdir client-dir")
machine.succeed("mkdir signer-dir")
with subtest("run binaries with --help"):
    for b in binaries:
        machine.succeed(b + " --help")


machine.succeed(f"{tezos_client} -d client-dir gen keys baker")


def pkill_background(binary):
    machine.succeed("pkill " + binary)


def run_node(network, use_tls):
    machine.succeed("rm -rf node-dir")
    machine.succeed("mkdir node-dir")
    if use_tls:
        machine.succeed(f"{openssl} genrsa 2048 > host.key")
        machine.succeed(
            f"{openssl} req -new -x509 -nodes -sha256 -days 365 -key host.key -out host.cert -subj '/'"
        )
    tls_args = " --rpc-tls=host.cert,host.key " if use_tls else " "
    machine.succeed(f"{tezos_node} config init --data-dir node-dir --network {network}")
    machine.succeed(f"{tezos_node} identity generate 1 --data-dir node-dir")
    machine.succeed(
        f"{tezos_node} run --data-dir node-dir --rpc-addr 127.0.0.1:8732 "
        + tls_args
        + "--no-bootstrap-peers --network "
        + network
        + " &"
    )
    tls_endpoint = (
        " --endpoint https://127.0.0.1:8732/ "
        if use_tls
        else " --endpoint http://127.0.0.1:8732/ "
    )
    machine.wait_until_succeeds(
        tezos_client + tls_endpoint + "rpc get chains/main/blocks/head/"
    )


def run_node_with_daemons(network, use_tls):
    run_node(network, use_tls)
    tls_endpoint = (
        " --endpoint https://127.0.0.1:8732/ "
        if use_tls
        else " --endpoint http://127.0.0.1:8732/ "
    )
    machine.succeed(
        f"{tezos_baker} -d client-dir"
        + tls_endpoint
        + "run with local node node-dir baker &"
    )
    machine.succeed(tezos_endorser + tls_endpoint + "-d client-dir run baker &")
    machine.succeed(tezos_accuser + tls_endpoint + "-d client-dir run &")


def kill_node_with_daemons():
    pkill_background("tezos-accuser")
    pkill_background("tezos-endorser")
    pkill_background("tezos-baker")
    pkill_background("tezos-node")


def test_node_with_daemons_scenario(network, use_tls=False):
    tls_endpoint = (
        " --endpoint https://127.0.0.1:8732/ "
        if use_tls
        else " --endpoint http://127.0.0.1:8732/ "
    )
    run_node_with_daemons(network, use_tls)
    machine.succeed(
        tezos_admin_client + tls_endpoint + "rpc get chains/main/blocks/head/"
    )
    kill_node_with_daemons()


with subtest("run node with daemons on florencenet"):
    test_node_with_daemons_scenario("florencenet")

with subtest("run node with daemons on mainnet"):
    test_node_with_daemons_scenario("mainnet")

with subtest("run node with daemons using tls"):
    test_node_with_daemons_scenario("mainnet", use_tls=True)

with subtest("test remote signer"):
    machine.succeed(f"{tezos_signer} -d signer-dir gen keys signer")
    signer_addr = machine.succeed(
        f'{tezos_signer} -d signer-dir show address signer | head -n 1 | sed -e s/^"Hash: "//g'
    )
    machine.succeed(
        f"{tezos_signer} -d signer-dir launch socket signer -a 127.0.0.1 -p 22000 &"
    )
    machine.succeed(
        f"{tezos_client} -d client-dir import secret key remote-signer-tcp tcp://127.0.0.1:22000/{signer_addr}"
    )

with subtest("test encode and decode JSON"):
    machine.succeed(f"{tezos_codec} encode timespan.system from 42.42")
    machine.succeed(f"{tezos_codec} decode timespan.system from 404535c28f5c28f6")
