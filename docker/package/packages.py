# SPDX-FileCopyrightText: 2020 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ
import os, shutil, sys, subprocess, json

from .model import Service, ServiceFile, SystemdUnit, Unit, OpamBasedPackage

networks = ["mainnet", "delphinet", "edonet"]

signer_units = [
    SystemdUnit(
        ServiceFile(Unit(after=["network.target"],
                         description="Tezos signer daemon running over TCP socket"),
                    Service(environment_file="/etc/default/tezos-signer-tcp",
                            environment=["ADDRESS=127.0.0.1", "PORT=8000", "TIMEOUT=1"],
                            exec_start="/usr/bin/tezos-signer-start launch socket signer " \
                            + " --address ${ADDRESS} --port ${PORT} --timeout ${TIMEOUT}",
                            state_directory="tezos", user="tezos")),
        suffix="tcp",
        startup_script="tezos-signer-start",
        config_file="tezos-signer.conf"),
    SystemdUnit(
        ServiceFile(Unit(after=["network.target"],
                         description="Tezos signer daemon running over UNIX socket"),
                    Service(environment_file="/etc/default/tezos-signer-unix",
                            environment=["SOCKET="],
                            exec_start="/usr/bin/tezos-signer-start launch local signer " \
                            + "--socket ${SOCKET}",
                            state_directory="tezos", user="tezos")),
        suffix="unix",
        startup_script="tezos-signer-start",
        config_file="tezos-signer.conf"),
    SystemdUnit(
        ServiceFile(Unit(after=["network.target"],
                         description="Tezos signer daemon running over HTTP"),
                    Service(environment_file="/etc/default/tezos-signer-http",
                            environment=["CERT_PATH=", "KEY_PATH=", "ADDRESS=127.0.0.1", "PORT=8080"],
                            exec_start="/usr/bin/tezos-signer-start launch http signer " \
                            + "--address ${ADDRESS} --port ${PORT}",
                            state_directory="tezos", user="tezos")),
        suffix="http",
        startup_script="tezos-signer-start",
        config_file="tezos-signer.conf"),
    SystemdUnit(
        ServiceFile(Unit(after=["network.target"],
                         description="Tezos signer daemon running over HTTPs"),
                    Service(environment_file="/etc/default/tezos-signer-https",
                            environment=["CERT_PATH=", "KEY_PATH=", "ADDRESS=127.0.0.1", "PORT=8080"],
                            exec_start="/usr/bin/tezos-signer-start launch https signer " \
                            + "${CERT_PATH} ${KEY_PATH} --address ${ADDRESS} --port ${PORT}",
                            state_directory="tezos", user="tezos")),
        suffix="https",
        startup_script="tezos-signer-start",
        config_file="tezos-signer.conf")
]

packages = [
    OpamBasedPackage("tezos-client",
                     "CLI client for interacting with tezos blockchain",
                     optional_opam_deps=["tls", "ledgerwallet-tezos"]),
    OpamBasedPackage("tezos-admin-client",
                     "Administration tool for the node",
                     optional_opam_deps=["tls"]),
    OpamBasedPackage("tezos-signer",
                     "A client to remotely sign operations or blocks",
                     optional_opam_deps=["tls", "ledgerwallet-tezos"],
                     systemd_units=signer_units),
    OpamBasedPackage("tezos-codec",
                     "A client to decode and encode JSON")
]


def mk_node_unit(suffix, env, desc):
    service_file = ServiceFile(Unit(after=["network.target"], requires=[],
                                    description=desc),
                               Service(environment=env,
                                       exec_start="/usr/bin/tezos-node-start",
                                       state_directory="tezos", user="tezos"
                               ))
    return SystemdUnit(suffix=suffix, service_file=service_file, startup_script="tezos-node-start")


node_units = []
common_node_env = ["NODE_RPC_ADDR=127.0.0.1:8732", "CERT_PATH=", "KEY_PATH="]
for network in networks:
    env = [f"DATA_DIR=/var/lib/tezos/node-{network}", f"NETWORK={network}"] + common_node_env
    node_units.append(mk_node_unit(suffix=network, env=env, desc=f"Tezos node {network}"))

node_units.append(mk_node_unit(suffix="custom", env=["DATA_DIR=/var/lib/tezos/node-custom",
                                                     "CUSTOM_NODE_CONFIG="] + common_node_env,
                               desc="Tezos node with custom config"))

packages.append(OpamBasedPackage("tezos-node",
                                 node_units,
                                 optional_opam_deps=[
                                     "tezos-embedded-protocol-001-PtCJ7pwo",
                                     "tezos-embedded-protocol-002-PsYLVpVv",
                                     "tezos-embedded-protocol-003-PsddFKi3",
                                     "tezos-embedded-protocol-004-Pt24m4xi",
                                     "tezos-embedded-protocol-005-PsBABY5H",
                                     "tezos-embedded-protocol-005-PsBabyM1",
                                     "tezos-embedded-protocol-006-PsCARTHA"]))

active_protocols = json.load(open(f"{os.path.dirname( __file__)}/../../protocols.json", "r"))["active"]

daemons = ["baker", "accuser", "endorser"]

daemon_decs = {
    "baker": "daemon for baking",
    "accuser": "daemon for accusing",
    "endorser": "daemon for endorsing"
}

default_testnets = {
    "007-PsDELPH1": "delphinet",
    "008-PtEdoTez": "edonet"
}

for proto in active_protocols:
    service_file_baker = ServiceFile(Unit(after=["network.target"],
                                          description="Tezos baker"),
                                     Service(environment_file=f"/etc/default/tezos-baker-{proto}",
                                             environment=[f"PROTOCOL={proto}"],
                                             exec_start="/usr/bin/tezos-baker-start",
                                             state_directory="tezos", user="tezos"))
    service_file_accuser = ServiceFile(Unit(after=["network.target"],
                                            description="Tezos accuser"),
                                       Service(environment_file=f"/etc/default/tezos-accuser-{proto}",
                                               environment=[f"PROTOCOL={proto}"],
                                               exec_start="/usr/bin/tezos-accuser-start",
                                               state_directory="tezos", user="tezos"))
    service_file_endorser = ServiceFile(Unit(after=["network.target"],
                                             description="Tezos endorser"),
                                        Service(environment_file=f"/etc/default/tezos-endorser-{proto}",
                                                environment=[f"PROTOCOL={proto}"],
                                                exec_start="/usr/bin/tezos-endorser-start",
                                                state_directory="tezos", user="tezos"))
    packages.append(OpamBasedPackage(f"tezos-baker-{proto}", "Daemon for baking",
                                     [SystemdUnit(service_file=service_file_baker,
                                                  startup_script="tezos-baker-start",
                                                  config_file="tezos-baker.conf")],
                                     proto,
                                     optional_opam_deps=["tls", "ledgerwallet-tezos"]))
    packages.append(OpamBasedPackage(f"tezos-accuser-{proto}", "Daemon for accusing",
                                     [SystemdUnit(service_file=service_file_accuser,
                                                  startup_script="tezos-accuser-start",
                                                  config_file="tezos-accuser.conf")],
                                     proto,
                                     optional_opam_deps=["tls", "ledgerwallet-tezos"]))
    packages.append(OpamBasedPackage(f"tezos-endorser-{proto}", "Daemon for endorsing",
                                     [SystemdUnit(service_file=service_file_endorser,
                                                  startup_script="tezos-endorser-start",
                                                  config_file="tezos-endorser.conf")],
                                     proto,
                                     optional_opam_deps=["tls", "ledgerwallet-tezos"]))

