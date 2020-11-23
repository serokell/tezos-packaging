# SPDX-FileCopyrightText: 2020 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ

from typing import List

# There are more possible fields, but only these are used by tezos services
class Service:
    def __init__(self, exec_start: str, state_directory:str, user: str,
                 environment_file: str=None, environment: List[str]=[]):
        self.environment_file = environment_file
        self.environment = environment
        self.exec_start = exec_start
        self.state_directory = state_directory
        self.user = user

class Unit:
    def __init__(self, after: List[str], description: str, requires: List[str]=[]):
        self.after = after
        self.requires = requires
        self.description = description

class ServiceFile:
    def __init__(self, unit: Unit, service:Service):
        self.unit = unit
        self.service = service

class SystemdUnit:
    def __init__(self, service_file:ServiceFile, startup_script:str, suffix:str=None,
                 config_file: str=None):
        self.suffix = suffix
        self.service_file = service_file
        self.startup_script = startup_script
        self.config_file = config_file

class Package:
    def __init__(self, name: str, desc: str, systemd_units: List[SystemdUnit]=[],
                 target_proto: str=None, optional_opam_deps=[]):
        self.name = name
        self.desc = desc
        self.systemd_units = systemd_units
        self.target_proto = target_proto
        self.optional_opam_deps = optional_opam_deps

def print_service_file(service_file: ServiceFile, out):
    after = "".join(map(lambda x: f"After={x}\n", service_file.unit.after))
    requires = "".join(map(lambda x: f"Requires={x}\n", service_file.unit.requires))
    environment = "".join(map(lambda x: f"Environment=\"{x}\"\n", service_file.service.environment))
    environment_file = "" if service_file.service.environment_file is None else f"EnvironmentFile={service_file.service.environment_file}"
    file_contents = f'''# SPDX-FileCopyrightText: 2020 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ
[Unit]
{after}{requires}Description={service_file.unit.description}
[Service]
{environment_file}
{environment}ExecStart={service_file.service.exec_start}
StateDirectory={service_file.service.state_directory}
User={service_file.service.user}
Group={service_file.service.user}
[Install]
WantedBy=multi-user.target
'''
    with open(out, 'w') as f:
        f.write(file_contents)
