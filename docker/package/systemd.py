# SPDX-FileCopyrightText: 2022 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA
from dataclasses import dataclass
from typing import List

# There are more possible fields, but only these are used by tezos services
@dataclass
class Service:
    exec_start: str
    state_directory: str
    user: str
    exec_start_pre: List[str] = None
    exec_start_post: List[str] = None
    exec_stop_post: List[str] = None
    timeout_start_sec: str = None
    environment_file: str = None
    environment: List[str] = None
    remain_after_exit: bool = False
    type_: str = None
    notify_access: str = None
    restart: str = None
    keyring_mode: str = None


@dataclass
class Unit:
    after: List[str]
    description: str
    requires: List[str] = None
    part_of: List[str] = None


@dataclass
class Install:
    wanted_by: List[str] = None


@dataclass
class ServiceFile:
    unit: Unit
    service: Service
    install: Install


@dataclass
class SystemdUnit:
    service_file: ServiceFile
    startup_script: str = None
    startup_script_source: str = None
    prestart_script: str = None
    prestart_script_source: str = None
    poststop_script: str = None
    poststop_script_source: str = None
    suffix: str = None
    config_file: str = None
    instances: List[str] = None


def print_service_file(service_file: ServiceFile, out):
    after = requires = part_of = environment = environment_file = wanted_by = ""
    exec_start_pres = exec_start_posts = exec_stop_posts = ""
    if service_file.unit.after is not None:
        after = "".join(f"After={x}\n" for x in service_file.unit.after)
    if service_file.unit.requires is not None:
        requires = "".join(f"Requires={x}\n" for x in service_file.unit.requires)
    if service_file.unit.part_of is not None:
        part_of = "".join(f"PartOf={x}\n" for x in service_file.unit.part_of)
    if service_file.service.environment is not None:
        environment = "".join(
            f'Environment="{x}"\n' for x in service_file.service.environment
        )
    if service_file.service.environment_file is not None:
        environment_file = f"EnvironmentFile={service_file.service.environment_file}"
    if service_file.install.wanted_by is not None:
        wanted_by = "".join(f"WantedBy={x}\n" for x in service_file.install.wanted_by)
    if service_file.service.exec_start_pre is not None:
        exec_start_pres = "\n".join(
            f"ExecStartPre={x}" for x in service_file.service.exec_start_pre
        )
    if service_file.service.exec_start_post is not None:
        exec_start_posts = "\n".join(
            f"ExecStartPost={x}" for x in service_file.service.exec_start_post
        )
    if service_file.service.exec_stop_post is not None:
        exec_stop_posts = "\n".join(
            f"ExecStopPost={x}" for x in service_file.service.exec_stop_post
        )
    file_contents = f"""# SPDX-FileCopyrightText: 2022 Oxhead Alpha
#
# SPDX-License-Identifier: LicenseRef-MIT-OA
[Unit]
{after}{requires}{part_of}Description={service_file.unit.description}
[Service]
{environment_file}
{environment}
{exec_start_pres}
{f"TimeoutStartSec={service_file.service.timeout_start_sec}" if service_file.service.timeout_start_sec is not None else ""}
ExecStart={service_file.service.exec_start}
{exec_start_posts}
{exec_stop_posts}
StateDirectory={service_file.service.state_directory}
User={service_file.service.user}
Group={service_file.service.user}
{"RemainAfterExit=yes" if service_file.service.remain_after_exit else ""}
{f"Type={service_file.service.type_}" if service_file.service.type_ is not None else ""}
{f"NotifyAccess={service_file.service.notify_access}" if service_file.service.notify_access is not None else ""}
{f"Restart={service_file.service.restart}" if service_file.service.restart is not None else ""}
{f"KeyringMode={service_file.service.keyring_mode}" if service_file.service.keyring_mode is not None else ""}
[Install]
{wanted_by}
"""
    with open(out, "w") as f:
        f.write(file_contents)
