# SPDX-FileCopyrightText: 2021 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ
from typing import List

# There are more possible fields, but only these are used by tezos services
class Service:
    def __init__(
        self,
        exec_start: str,
        state_directory: str,
        user: str,
        exec_start_pre: str = None,
        exec_start_post: str = None,
        exec_stop_post: str = None,
        timeout_start_sec: str = None,
        environment_file: str = None,
        environment: List[str] = [],
        remain_after_exit: bool = False,
        type_: str = None,
        restart: str = None,
        keyring_mode: str = None,
    ):
        self.environment_file = environment_file
        self.environment = environment
        self.exec_start = exec_start
        self.exec_start_pre = exec_start_pre
        self.exec_start_post = exec_start_post
        self.exec_stop_post = exec_stop_post
        self.timeout_start_sec = timeout_start_sec
        self.state_directory = state_directory
        self.user = user
        self.remain_after_exit = remain_after_exit
        self.type_ = type_
        self.restart = restart
        self.keyring_mode = keyring_mode


class Unit:
    def __init__(
        self,
        after: List[str],
        description: str,
        requires: List[str] = [],
        part_of: List[str] = [],
    ):
        self.after = after
        self.requires = requires
        self.part_of = part_of
        self.description = description


class Install:
    def __init__(self, wanted_by: List[str] = []):
        self.wanted_by = wanted_by


class ServiceFile:
    def __init__(self, unit: Unit, service: Service, install: Install):
        self.unit = unit
        self.service = service
        self.install = install


class SystemdUnit:
    def __init__(
        self,
        service_file: ServiceFile,
        startup_script: str = None,
        startup_script_source: str = None,
        prestart_script: str = None,
        prestart_script_source: str = None,
        suffix: str = None,
        config_file: str = None,
        instances: List[str] = [],
    ):
        self.suffix = suffix
        self.service_file = service_file
        self.startup_script = startup_script
        self.startup_script_source = startup_script_source
        self.prestart_script = prestart_script
        self.prestart_script_source = prestart_script_source
        self.config_file = config_file
        self.instances = instances


def print_service_file(service_file: ServiceFile, out):
    after = "".join(f"After={x}\n" for x in service_file.unit.after)
    requires = "".join(f"Requires={x}\n" for x in service_file.unit.requires)
    part_of = "".join(f"PartOf={x}\n" for x in service_file.unit.part_of)
    environment = "".join(
        f'Environment="{x}"\n' for x in service_file.service.environment
    )
    environment_file = (
        ""
        if service_file.service.environment_file is None
        else f"EnvironmentFile={service_file.service.environment_file}"
    )
    wanted_by = "".join(f"WantedBy={x}\n" for x in service_file.install.wanted_by)
    exec_start_pres = (
        "\n".join(f"ExecStartPre={x}" for x in service_file.service.exec_start_pre)
        if service_file.service.exec_start_pre is not None
        else ""
    )
    exec_start_posts = (
        "\n".join(f"ExecStartPost={x}" for x in service_file.service.exec_start_post)
        if service_file.service.exec_start_post is not None
        else ""
    )
    exec_stop_posts = (
        "\n".join(f"ExecStopPost={x}" for x in service_file.service.exec_stop_post)
        if service_file.service.exec_stop_post is not None
        else ""
    )
    file_contents = f"""# SPDX-FileCopyrightText: 2020 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ
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
{f"Restart={service_file.service.restart}" if service_file.service.restart is not None else ""}
{f"KeyringMode={service_file.service.keyring_mode}" if service_file.service.keyring_mode is not None else ""}
[Install]
{wanted_by}
"""
    with open(out, "w") as f:
        f.write(file_contents)
