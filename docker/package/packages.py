# SPDX-FileCopyrightText: 2020 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ
import os, shutil, sys, subprocess, json

from .model import Service, ServiceFile, SystemdUnit, Unit, Install, OpamBasedPackage, TezosSaplingParamsPackage, TezosBakingServicesPackage

networks = ["mainnet", "edo2net", "florencenet"]
networks_protos = {
    "mainnet": ["008-PtEdo2Zk", "009-PsFLoren"],
    "edo2net": ["008-PtEdo2Zk"],
    "florencenet": ["009-PsFLoren"]
}

signer_units = [
    SystemdUnit(
        ServiceFile(Unit(after=["network.target"],
                         description="Tezos signer daemon running over TCP socket"),
                    Service(environment_file="/etc/default/tezos-signer-tcp",
                            environment=["ADDRESS=127.0.0.1", "PORT=8000", "TIMEOUT=1"],
                            exec_start="/usr/bin/tezos-signer-start launch socket signer " \
                            + " --address ${ADDRESS} --port ${PORT} --timeout ${TIMEOUT}",
                            state_directory="tezos", user="tezos"),
                    Install(wanted_by=["multi-user.target"])),
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
                            state_directory="tezos", user="tezos"),
                    Install(wanted_by=["multi-user.target"])),
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
                            state_directory="tezos", user="tezos"),
                    Install(wanted_by=["multi-user.target"])),
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
                            state_directory="tezos", user="tezos"),
                    Install(wanted_by=["multi-user.target"])),
        suffix="https",
        startup_script="tezos-signer-start",
        config_file="tezos-signer.conf")
]

ledger_udev_postinst = open(f"{os.path.dirname( __file__)}/scripts/udev-rules", 'r').read()

packages = [
    OpamBasedPackage("tezos-client",
                     "CLI client for interacting with tezos blockchain",
                     optional_opam_deps=["tls", "ledgerwallet-tezos"],
                     additional_native_deps=["tezos-sapling-params", "udev"],
                     postinst_steps=ledger_udev_postinst),
    OpamBasedPackage("tezos-admin-client",
                     "Administration tool for the node",
                     optional_opam_deps=["tls"]),
    OpamBasedPackage("tezos-signer",
                     "A client to remotely sign operations or blocks",
                     optional_opam_deps=["tls", "ledgerwallet-tezos"],
                     additional_native_deps=["udev"],
                     systemd_units=signer_units,
                     postinst_steps=ledger_udev_postinst),
    OpamBasedPackage("tezos-codec",
                     "A client to decode and encode JSON")
]

postinst_steps_common = '''
useradd --home-dir /var/lib/tezos tezos || true
'''


def mk_node_unit(suffix, env, desc):
    service_file = ServiceFile(Unit(after=["network.target", f"tezos-baking-{suffix}.service"],
                                    requires=[], description=desc,
                                    part_of=[f"tezos-baking-{suffix}.service"]),
                               Service(environment=env,
                                       exec_start="/usr/bin/tezos-node-start",
                                       exec_start_pre=["/usr/bin/tezos-node-prestart"],
                                       timeout_start_sec="450s",
                                       state_directory="tezos", user="tezos"
                               ),
                               Install(wanted_by=["multi-user.target"]))
    return SystemdUnit(suffix=suffix, service_file=service_file, startup_script="tezos-node-start",
                       prestart_script="tezos-node-prestart")

node_units = []
node_postinst_steps = postinst_steps_common
node_postrm_steps = ""
common_node_env = ["NODE_RPC_ADDR=127.0.0.1:8732", "CERT_PATH=", "KEY_PATH="]
for network in networks:
    env = [f"DATA_DIR=/var/lib/tezos/node-{network}", f"NETWORK={network}"] + common_node_env
    node_units.append(mk_node_unit(suffix=network, env=env, desc=f"Tezos node {network}"))
    node_postinst_steps += f'''mkdir -p /var/lib/tezos/node-{network}
[ ! -f /var/lib/tezos/node-{network}/config.json ] && tezos-node config init --data-dir /var/lib/tezos/node-{network} --network {network}
chown -R tezos:tezos /var/lib/tezos/node-{network}

cat > /usr/bin/tezos-node-{network} <<- 'EOM'
#! /usr/bin/env bash

TEZOS_NODE_DIR="$(cat $(systemctl show -p FragmentPath tezos-node-{network}.service | cut -d'=' -f2) | grep 'DATA_DIR' | cut -d '=' -f3 | cut -d '"' -f1)" tezos-node "$@"
EOM
chmod +x /usr/bin/tezos-node-{network}
'''
    node_postrm_steps += f'''
rm -f /usr/bin/tezos-node-{network}
'''

# Add custom config service
node_units.append(mk_node_unit(suffix="custom", env=["DATA_DIR=/var/lib/tezos/node-custom",
                                                     "CUSTOM_NODE_CONFIG="] + common_node_env,
                               desc="Tezos node with custom config"))
node_postinst_steps += "mkdir -p /var/lib/tezos/node-custom\n"

packages.append(OpamBasedPackage("tezos-node",
                                 "Entry point for initializing, configuring and running a Tezos node",
                                 node_units,
                                 optional_opam_deps=[
                                     "tezos-embedded-protocol-001-PtCJ7pwo",
                                     "tezos-embedded-protocol-002-PsYLVpVv",
                                     "tezos-embedded-protocol-003-PsddFKi3",
                                     "tezos-embedded-protocol-004-Pt24m4xi",
                                     "tezos-embedded-protocol-005-PsBABY5H",
                                     "tezos-embedded-protocol-005-PsBabyM1",
                                     "tezos-embedded-protocol-006-PsCARTHA"],
                                 postinst_steps=node_postinst_steps,
                                 postrm_steps=node_postrm_steps,
                                 additional_native_deps=["tezos-sapling-params"]))

active_protocols = json.load(open(f"{os.path.dirname( __file__)}/../../protocols.json", "r"))["active"]

daemons = ["baker", "accuser", "endorser"]

daemon_decs = {
    "baker": "daemon for baking",
    "accuser": "daemon for accusing",
    "endorser": "daemon for endorsing"
}

daemon_postinst_common = postinst_steps_common + "\nmkdir -p /var/lib/tezos/.tezos-client\nchown -R tezos:tezos /var/lib/tezos/.tezos-client\n"

for proto in active_protocols:
    daemons_instances = \
        [network for network, protos in networks_protos.items() if proto in protos]
    baker_startup_script = f"/usr/bin/tezos-baker-{proto.lower()}-start"
    endorser_startup_script = f"/usr/bin/tezos-endorser-{proto.lower()}-start"
    accuser_startup_script = f"/usr/bin/tezos-accuser-{proto.lower()}-start"
    service_file_baker = ServiceFile(Unit(after=["network.target"],
                                          description="Tezos baker"),
                                     Service(environment_file=f"/etc/default/tezos-baker-{proto}",
                                             environment=[f"PROTOCOL={proto}", "NODE_DATA_DIR="],
                                             exec_start_pre=["+/usr/bin/setfacl -m u:tezos:rwx /run/systemd/ask-password"],
                                             exec_start=baker_startup_script,
                                             exec_stop_post=["+/usr/bin/setfacl -x u:tezos /run/systemd/ask-password"],
                                             state_directory="tezos", user="tezos", type_="forking",
                                             keyring_mode="shared"),
                                     Install(wanted_by=["multi-user.target"]))
    service_file_baker_instantiated = \
        ServiceFile(Unit(after=["network.target", "tezos-node-%i.service", "tezos-baking-%i.service"],
                         requires=["tezos-node-%i.service"],
                         part_of=["tezos-baking-%i.service"],
                         description="Instantiated tezos baker daemon service"),
                    Service(environment_file="/etc/default/tezos-baking-%i",
                            environment=[f"PROTOCOL={proto}", "NODE_DATA_DIR=/var/lib/tezos/node-%i"],
                            exec_start=baker_startup_script,
                            state_directory="tezos", user="tezos", restart="on-failure",
                            type_="forking", keyring_mode="shared"),
                    Install(wanted_by=["multi-user.target"]))
    service_file_accuser = ServiceFile(Unit(after=["network.target"],
                                            description="Tezos accuser"),
                                       Service(environment_file=f"/etc/default/tezos-accuser-{proto}",
                                               environment=[f"PROTOCOL={proto}"],
                                               exec_start=accuser_startup_script,
                                               state_directory="tezos", user="tezos"),
                                       Install(wanted_by=["multi-user.target"]))
    service_file_accuser_instantiated = \
        ServiceFile(Unit(after=["network.target", "tezos-node-%i.service", "tezos-baking-%i.service"],
                         requires=["tezos-node-%i.service"],
                         part_of=["tezos-baking-%i.service"],
                         description="Instantiated tezos accuser daemon service"),
                    Service(environment_file="/etc/default/tezos-baking-%i",
                            environment=[f"PROTOCOL={proto}"],
                            exec_start=accuser_startup_script,
                            state_directory="tezos", user="tezos", restart="on-failure"),
                    Install(wanted_by=["multi-user.target"]))
    service_file_endorser = ServiceFile(Unit(after=["network.target"],
                                             description="Tezos endorser"),
                                        Service(environment_file=f"/etc/default/tezos-endorser-{proto}",
                                                environment=[f"PROTOCOL={proto}"],
                                                exec_start_pre=["+/usr/bin/setfacl -m u:tezos:rwx /run/systemd/ask-password"],
                                                exec_start=endorser_startup_script,
                                                exec_stop_post=["+/usr/bin/setfacl -x u:tezos /run/systemd/ask-password"],
                                                state_directory="tezos", user="tezos", type_="forking",
                                                keyring_mode="shared"),
                                        Install(wanted_by=["multi-user.target"]))
    service_file_endorser_instantiated = \
        ServiceFile(Unit(after=["network.target", "tezos-node-%i.service", "tezos-baking-%i.service"],
                         requires=["tezos-node-%i.service"],
                         part_of=["tezos-baking-%i.service"],
                         description="Instantiated tezos endorser daemon service"),
                    Service(environment_file="/etc/default/tezos-baking-%i",
                            environment=[f"PROTOCOL={proto}"],
                            exec_start=endorser_startup_script,
                            state_directory="tezos", user="tezos", restart="on-failure",
                            type_="forking", keyring_mode="shared"),
                    Install(wanted_by=["multi-user.target"]))
    packages.append(OpamBasedPackage(f"tezos-baker-{proto}", "Daemon for baking",
                                     [SystemdUnit(service_file=service_file_baker,
                                                  startup_script=baker_startup_script.split('/')[-1],
                                                  startup_script_source="tezos-baker-start",
                                                  config_file="tezos-baker.conf"),
                                      SystemdUnit(service_file=service_file_baker_instantiated,
                                                  startup_script=baker_startup_script.split('/')[-1],
                                                  startup_script_source="tezos-baker-start",
                                                  instances=daemons_instances)],
                                     proto,
                                     optional_opam_deps=["tls", "ledgerwallet-tezos"],
                                     postinst_steps= daemon_postinst_common + ledger_udev_postinst,
                                     additional_native_deps=["tezos-sapling-params", "tezos-client", "acl", "udev"]))
    packages.append(OpamBasedPackage(f"tezos-accuser-{proto}", "Daemon for accusing",
                                     [SystemdUnit(service_file=service_file_accuser,
                                                  startup_script=accuser_startup_script.split('/')[-1],
                                                  startup_script_source="tezos-accuser-start",
                                                  config_file="tezos-accuser.conf"),
                                      SystemdUnit(service_file=service_file_accuser_instantiated,
                                                  startup_script=accuser_startup_script.split('/')[-1],
                                                  startup_script_source="tezos-accuser-start",
                                                  instances=daemons_instances)],
                                     proto,
                                     optional_opam_deps=["tls", "ledgerwallet-tezos"],
                                     additional_native_deps=["udev"],
                                     postinst_steps= daemon_postinst_common + ledger_udev_postinst))
    packages.append(OpamBasedPackage(f"tezos-endorser-{proto}", "Daemon for endorsing",
                                     [SystemdUnit(service_file=service_file_endorser,
                                                  startup_script=endorser_startup_script.split('/')[-1],
                                                  startup_script_source="tezos-endorser-start",
                                                  config_file="tezos-endorser.conf"),
                                      SystemdUnit(service_file=service_file_endorser_instantiated,
                                                  startup_script=endorser_startup_script.split('/')[-1],
                                                  startup_script_source="tezos-endorser-start",
                                                  instances=daemons_instances)],
                                     proto,
                                     optional_opam_deps=["tls", "ledgerwallet-tezos"],
                                     postinst_steps= daemon_postinst_common + ledger_udev_postinst,
                                     additional_native_deps=["tezos-client", "acl", "udev"]))

packages.append(TezosSaplingParamsPackage())
packages.append(TezosBakingServicesPackage(
    target_networks=networks,
    network_protos=networks_protos
    ))
