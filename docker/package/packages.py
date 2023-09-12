# SPDX-FileCopyrightText: 2021 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA
import os, json, stat

from .meta import packages_meta

from .model import (
    AdditionalScript,
    TezosBinaryPackage,
    TezosSaplingParamsPackage,
    TezosBakingServicesPackage,
)

from .systemd import Service, ServiceFile, SystemdUnit, Unit, Install
from collections import ChainMap

# Testnets are either supported by the tezos-node directly or have known URL with
# the config
networks = {
    "mainnet": "mainnet",
    "ghostnet": "ghostnet",
    "nairobinet": "https://teztnets.xyz/nairobinet",
    "oxfordnet": "https://teztnets.xyz/oxfordnet",
}
networks_protos = {
    "mainnet": ["PtNairob"],
    "ghostnet": ["PtNairob"],
    "nairobinet": ["PtNairob"],
    "oxfordnet": ["Proxford"],
}

protocol_numbers = {
    "PtNairob": "017",
    "Proxford": "018",
}

signer_units = [
    SystemdUnit(
        ServiceFile(
            Unit(
                after=["network.target"],
                description="Tezos signer daemon running over TCP socket",
            ),
            Service(
                environment_files=["/etc/default/tezos-signer-tcp"],
                exec_start="/usr/bin/tezos-signer-start launch socket signer "
                + " --address ${ADDRESS} --port ${PORT} --timeout ${TIMEOUT}",
                state_directory="tezos",
                user="tezos",
            ),
            Install(wanted_by=["multi-user.target"]),
        ),
        suffix="tcp",
        startup_script="tezos-signer-start",
        config_file="tezos-signer.conf",
        config_file_append=['ADDRESS="127.0.0.1"', 'PORT="8000"', 'TIMEOUT="1"'],
    ),
    SystemdUnit(
        ServiceFile(
            Unit(
                after=["network.target"],
                description="Tezos signer daemon running over UNIX socket",
            ),
            Service(
                environment_files=["/etc/default/tezos-signer-unix"],
                exec_start="/usr/bin/tezos-signer-start launch local signer "
                + "--socket ${SOCKET}",
                state_directory="tezos",
                user="tezos",
            ),
            Install(wanted_by=["multi-user.target"]),
        ),
        suffix="unix",
        startup_script="tezos-signer-start",
        config_file="tezos-signer.conf",
        config_file_append=['SOCKET=""'],
    ),
    SystemdUnit(
        ServiceFile(
            Unit(
                after=["network.target"],
                description="Tezos signer daemon running over HTTP",
            ),
            Service(
                environment_files=["/etc/default/tezos-signer-http"],
                exec_start="/usr/bin/tezos-signer-start launch http signer "
                + "--address ${ADDRESS} --port ${PORT}",
                state_directory="tezos",
                user="tezos",
            ),
            Install(wanted_by=["multi-user.target"]),
        ),
        suffix="http",
        startup_script="tezos-signer-start",
        config_file="tezos-signer.conf",
        config_file_append=[
            'CERT_PATH="',
            'KEY_PATH=""',
            'ADDRESS="127.0.0.1"',
            'PORT="8080"',
        ],
    ),
    SystemdUnit(
        ServiceFile(
            Unit(
                after=["network.target"],
                description="Tezos signer daemon running over HTTPs",
            ),
            Service(
                environment_files=["/etc/default/tezos-signer-https"],
                exec_start="/usr/bin/tezos-signer-start launch https signer "
                + "${CERT_PATH} ${KEY_PATH} --address ${ADDRESS} --port ${PORT}",
                state_directory="tezos",
                user="tezos",
            ),
            Install(wanted_by=["multi-user.target"]),
        ),
        suffix="https",
        startup_script="tezos-signer-start",
        config_file="tezos-signer.conf",
        config_file_append=[
            'CERT_PATH="',
            'KEY_PATH=""',
            'ADDRESS="127.0.0.1"',
            'PORT="8080"',
        ],
    ),
]

postinst_steps_common = """
if [ -z $(getent passwd tezos) ]; then
    useradd -r -s /bin/false -m -d /var/lib/tezos tezos
    chmod 0755 /var/lib/tezos
fi
"""

ledger_udev_postinst = open(
    f"{os.path.dirname(__file__)}/scripts/udev-rules", "r"
).read()

packages = [
    {
        "tezos-client": TezosBinaryPackage(
            "tezos-client",
            "CLI client for interacting with tezos blockchain",
            meta=packages_meta,
            additional_native_deps=["tezos-sapling-params", "udev"],
            postinst_steps=postinst_steps_common + ledger_udev_postinst,
            dune_filepath="src/bin_client/main_client.exe",
        )
    },
    {
        "tezos-admin-client": TezosBinaryPackage(
            "tezos-admin-client",
            "Administration tool for the node",
            meta=packages_meta,
            dune_filepath="src/bin_client/main_admin.exe",
        )
    },
    {
        "tezos-signer": TezosBinaryPackage(
            "tezos-signer",
            "A client to remotely sign operations or blocks",
            meta=packages_meta,
            additional_native_deps=["udev"],
            systemd_units=signer_units,
            postinst_steps=postinst_steps_common + ledger_udev_postinst,
            dune_filepath="src/bin_signer/main_signer.exe",
        )
    },
    {
        "tezos-codec": TezosBinaryPackage(
            "tezos-codec",
            "A client to decode and encode JSON",
            meta=packages_meta,
            dune_filepath="src/bin_codec/codec.exe",
        )
    },
    {
        "tezos-dac-client": TezosBinaryPackage(
            "tezos-dac-client",
            "A Data Availability Committee Tezos client",
            meta=packages_meta,
            dune_filepath="src/bin_dac_client/main_dac_client.exe",
        )
    },
    {
        "tezos-dac-node": TezosBinaryPackage(
            "tezos-dac-node",
            "A Data Availability Committee Tezos node",
            meta=packages_meta,
            dune_filepath="src/bin_dac_node/main_dac.exe",
        )
    },
    {
        "tezos-smart-rollup-wasm-debugger": TezosBinaryPackage(
            "tezos-smart-rollup-wasm-debugger",
            "Smart contract rollup wasm debugger",
            meta=packages_meta,
            dune_filepath="src/bin_wasm_debugger/main_wasm_debugger.exe",
        )
    },
]


def mk_node_unit(
    suffix,
    config_file_append,
    desc,
    instantiated=False,
    dependencies_suffix=None,
):
    dependencies_suffix = suffix if dependencies_suffix is None else dependencies_suffix
    service_file = ServiceFile(
        Unit(
            after=["network.target", f"tezos-baking-{dependencies_suffix}.service"],
            requires=[],
            description=desc,
            part_of=[f"tezos-baking-{dependencies_suffix}.service"],
        ),
        Service(
            environment_files=[f"/etc/default/tezos-node-{suffix}"],
            exec_start="/usr/bin/tezos-node-start",
            exec_start_pre=["/usr/bin/tezos-node-prestart"],
            timeout_start_sec="2400s",
            state_directory="tezos",
            user="tezos",
            type_="notify",
            notify_access="all",
        ),
        Install(wanted_by=["multi-user.target"]),
    )
    return SystemdUnit(
        suffix=suffix,
        service_file=service_file,
        startup_script="tezos-node-start",
        prestart_script="tezos-node-prestart",
        instances=[] if instantiated else None,
        config_file="tezos-node.conf",
        config_file_append=config_file_append,
    )


node_units = []
node_postinst_steps = postinst_steps_common
node_additional_scripts = []
for network, network_config in networks.items():
    config_file_append = [
        f'TEZOS_NODE_DIR="/var/lib/tezos/node-{network}"',
        f'NETWORK="{network_config}"',
    ]
    node_units.append(
        mk_node_unit(
            suffix=network,
            config_file_append=config_file_append,
            desc=f"Tezos node {network}",
        )
    )
    node_additional_scripts.append(
        AdditionalScript(
            name=f"octez-node-{network}",
            symlink_name=f"tezos-node-{network}",
            local_file_name="octez-node-wrapper",
            transform=lambda x, network=network: x.replace("{network}", network),
        )
    )
    node_postinst_steps += f"""
mkdir -p /var/lib/tezos/node-{network}
[ ! -f /var/lib/tezos/node-{network}/config.json ] && octez-node config init --data-dir /var/lib/tezos/node-{network} --network {network_config}
chown -R tezos:tezos /var/lib/tezos/node-{network}
"""

# Add custom config service
custom_node_unit = mk_node_unit(
    suffix="custom",
    config_file_append=[
        'TEZOS_NODE_DIR="/var/lib/tezos/node-custom"',
        'CUSTOM_NODE_CONFIG=""',
    ],
    desc="Tezos node with custom config",
)
custom_node_unit.poststop_script = "tezos-node-custom-poststop"
node_units.append(custom_node_unit)
node_postinst_steps += "mkdir -p /var/lib/tezos/node-custom\n"
# Add instantiated custom config service
custom_node_instantiated = mk_node_unit(
    suffix="custom",
    config_file_append=[
        "TEZOS_NODE_DIR=/var/lib/tezos/node-custom@%i",
        "CUSTOM_NODE_CONFIG=",
        'RESET_ON_STOP=""',
    ],
    desc="Tezos node with custom config",
    instantiated=True,
    dependencies_suffix="custom@%i",
)
custom_node_instantiated.poststop_script = "tezos-node-custom-poststop"
node_units.append(custom_node_instantiated)


packages.append(
    {
        "tezos-node": TezosBinaryPackage(
            "tezos-node",
            "Entry point for initializing, configuring and running a Tezos node",
            meta=packages_meta,
            systemd_units=node_units,
            postinst_steps=node_postinst_steps,
            additional_native_deps=[
                "tezos-sapling-params",
                "curl",
                {"ubuntu": "netbase"},
            ],
            additional_scripts=node_additional_scripts,
            dune_filepath="src/bin_node/main.exe",
        )
    }
)

protocols_json = json.load(
    open(f"{os.path.dirname( __file__)}/../../protocols.json", "r")
)

active_protocols = protocols_json["active"]

daemons = ["baker", "accuser"]

daemon_decs = {
    "baker": "daemon for baking",
    "accuser": "daemon for accusing",
}

daemon_postinst_common = (
    postinst_steps_common
    + """
mkdir -p /var/lib/tezos/.tezos-client
chown -R tezos:tezos /var/lib/tezos/.tezos-client
"""
)


for proto in active_protocols:
    proto_snake_case = protocol_numbers[proto] + "_" + proto
    daemons_instances = [
        network for network, protos in networks_protos.items() if proto in protos
    ]
    baker_startup_script = f"/usr/bin/tezos-baker-{proto.lower()}-start"
    accuser_startup_script = f"/usr/bin/tezos-accuser-{proto.lower()}-start"
    service_file_baker = ServiceFile(
        Unit(after=["network.target"], description="Tezos baker"),
        Service(
            # The node settings for a generic baker are defined in its own
            # 'EnvironmentFile', as we can't tell the network from the protocol
            # alone, nor what node this might connect to
            environment_files=[f"/etc/default/tezos-baker-{proto}"],
            environment=[f"PROTOCOL={proto}"],
            exec_start_pre=[
                "+/usr/bin/setfacl -m u:tezos:rwx /run/systemd/ask-password"
            ],
            exec_start=baker_startup_script,
            exec_stop_post=["+/usr/bin/setfacl -x u:tezos /run/systemd/ask-password"],
            state_directory="tezos",
            user="tezos",
            type_="forking",
            keyring_mode="shared",
        ),
        Install(wanted_by=["multi-user.target"]),
    )
    service_file_baker_instantiated = ServiceFile(
        Unit(
            after=[
                "network.target",
                "tezos-node-%i.service",
                "tezos-baking-%i.service",
            ],
            requires=["tezos-node-%i.service"],
            part_of=["tezos-baking-%i.service"],
            description="Instantiated tezos baker daemon service",
        ),
        Service(
            environment_files=[
                "/etc/default/tezos-baking-%i",
                "/etc/default/tezos-node-%i",
            ],
            environment=[f"PROTOCOL={proto}"],
            exec_start=baker_startup_script,
            state_directory="tezos",
            user="tezos",
            restart="on-failure",
            type_="forking",
            keyring_mode="shared",
        ),
        Install(wanted_by=["multi-user.target"]),
    )
    service_file_accuser = ServiceFile(
        Unit(after=["network.target"], description="Tezos accuser"),
        Service(
            environment_files=[f"/etc/default/tezos-accuser-{proto}"],
            environment=[f"PROTOCOL={proto}"],
            exec_start=accuser_startup_script,
            state_directory="tezos",
            user="tezos",
        ),
        Install(wanted_by=["multi-user.target"]),
    )
    service_file_accuser_instantiated = ServiceFile(
        Unit(
            after=[
                "network.target",
                "tezos-node-%i.service",
                "tezos-baking-%i.service",
            ],
            requires=["tezos-node-%i.service"],
            part_of=["tezos-baking-%i.service"],
            description="Instantiated tezos accuser daemon service",
        ),
        Service(
            environment_files=["/etc/default/tezos-baking-%i"],
            environment=[f"PROTOCOL={proto}"],
            exec_start=accuser_startup_script,
            state_directory="tezos",
            user="tezos",
            restart="on-failure",
        ),
        Install(wanted_by=["multi-user.target"]),
    )
    packages.append(
        {
            f"tezos-baker-{proto}": TezosBinaryPackage(
                f"tezos-baker-{proto}",
                "Daemon for baking",
                meta=packages_meta,
                systemd_units=[
                    SystemdUnit(
                        service_file=service_file_baker,
                        startup_script=baker_startup_script.split("/")[-1],
                        startup_script_source="tezos-baker-start",
                        config_file="tezos-baker.conf",
                    ),
                    SystemdUnit(
                        service_file=service_file_baker_instantiated,
                        startup_script=baker_startup_script.split("/")[-1],
                        startup_script_source="tezos-baker-start",
                        instances=daemons_instances,
                    ),
                ],
                target_proto=proto,
                postinst_steps=daemon_postinst_common,
                additional_native_deps=[
                    "tezos-sapling-params",
                    "tezos-client",
                    "acl",
                    "udev",
                ],
                dune_filepath=f"src/proto_{proto_snake_case}/bin_baker/main_baker_{proto_snake_case}.exe",
            )
        }
    )
    packages.append(
        {
            f"tezos-accuser-{proto}": TezosBinaryPackage(
                f"tezos-accuser-{proto}",
                "Daemon for accusing",
                meta=packages_meta,
                systemd_units=[
                    SystemdUnit(
                        service_file=service_file_accuser,
                        startup_script=accuser_startup_script.split("/")[-1],
                        startup_script_source="tezos-accuser-start",
                        config_file="tezos-accuser.conf",
                    ),
                    SystemdUnit(
                        service_file=service_file_accuser_instantiated,
                        startup_script=accuser_startup_script.split("/")[-1],
                        startup_script_source="tezos-accuser-start",
                        instances=daemons_instances,
                    ),
                ],
                target_proto=proto,
                additional_native_deps=["udev"],
                postinst_steps=daemon_postinst_common,
                dune_filepath=f"src/proto_{proto_snake_case}/bin_accuser/main_accuser_{proto_snake_case}.exe",
            )
        }
    )

packages.append(
    {
        "tezos-sapling-params": TezosSaplingParamsPackage(
            meta=packages_meta,
            params_revision="95911b0639ff01807b8fd7b9e36d508e657d80a8",
        )
    }
)

packages.append(
    {
        "tezos-baking": TezosBakingServicesPackage(
            target_networks=networks.keys(),
            network_protos=networks_protos,
            meta=packages_meta,
            additional_native_deps=[
                f"tezos-baker-{proto}" for proto in active_protocols
            ]
            + ["tezos-node", "acl", "wget"],
        )
    }
)


def mk_rollup_packages(*protos):
    def mk_units(proto):
        startup_script = f"/usr/bin/tezos-sc-rollup-node-{proto}-start"
        service_file = ServiceFile(
            Unit(after=["network.target"], description=f"Tezos smart rollup node"),
            Service(
                environment_files=[f"/etc/default/tezos-smart-rollup-node-{proto}"],
                environment=[f"PROTOCOL={proto}", f"TYPE=sc"],
                exec_start_pre=[
                    "+/usr/bin/setfacl -m u:tezos:rwx /run/systemd/ask-password"
                ],
                exec_start=startup_script,
                exec_stop_post=[
                    "+/usr/bin/setfacl -x u:tezos /run/systemd/ask-password"
                ],
                state_directory="tezos",
                user="tezos",
                type_="forking",
                keyring_mode="shared",
            ),
            Install(wanted_by=["multi-user.target"]),
        )
        return [
            SystemdUnit(
                service_file=service_file,
                startup_script=startup_script.split("/")[-1],
                startup_script_source="tezos-rollup-node-start",
                config_file="tezos-rollup-node.conf",
            ),
        ]

    def mk_rollup_package(name, proto):
        proto_snake_case = protocol_numbers[proto] + "_" + proto
        return TezosBinaryPackage(
            f"tezos-smart-rollup-{name}-{proto}",
            f"Tezos smart rollup {name} using {proto}",
            meta=packages_meta,
            systemd_units=mk_units(proto) if name == "node" else [],
            target_proto=proto,
            additional_native_deps=[
                "tezos-client",
                "tezos-node",
                "tezos-sapling-params",
            ],
            postinst_steps=daemon_postinst_common,
            dune_filepath=f"src/proto_{proto_snake_case}/bin_sc_rollup_{name}/main_sc_rollup_{name}_{proto_snake_case}.exe",
        )

    packages = ["node", "client"]
    return [
        {f"tezos-smart-rollup-{name}-{proto}": mk_rollup_package(name, proto)}
        for name in packages
        for proto in protos
    ]


packages.extend(mk_rollup_packages("PtNairob", "Proxford"))

packages = dict(ChainMap(*packages))
