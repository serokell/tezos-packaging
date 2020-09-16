# SPDX-FileCopyrightText: 2020 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: MPL-2.0

import sys

from typing import List

# There are more possible fields, but only these are used by tezos services
class Unit:
    def __init__(self, after: List[str], requires: List[str], description: str):
        self.after = after
        self.requires = requires
        self.description = description

# There are more possible fields, but only these are used by tezos services
class Service:
    def __init__(self, environment_file: str, environment: List[str],
                 exec_start: str, state_directory:str, user: str):
        self.environment_file = environment_file
        self.environment = environment
        self.exec_start = exec_start
        self.state_directory = state_directory
        self.user = user

class ServiceFile:
    def __init__(self, unit: Unit, service:Service):
        self.unit = unit
        self.service = service

def gen_services(proto="stub"):
    services = {
        "tezos-node":
        ServiceFile(Unit(after=["network.target"], requires=[], description="Tezos node"),
                    Service(environment_file="/etc/default/tezos-node", environment=[],
                            exec_start="/usr/bin/tezos-node-start", state_directory="tezos", user="tezos")),
        "tezos-baker":
        ServiceFile(Unit(after=["network.target", "tezos-node.service"], requires=["tezos-node.service"],
                        description="Tezos baker"),
                    Service(environment_file=f"/etc/default/tezos-baker-{proto}",
                            environment=[f"PROTOCOL={proto}"], exec_start="/usr/bin/tezos-baker-start",
                            state_directory="tezos", user="tezos")),
        "tezos-accuser":
        ServiceFile(Unit(after=["network.target"], requires=[],
                        description="Tezos accuser"),
                    Service(environment_file=f"/etc/default/tezos-accuser-{proto}",
                            environment=[f"PROTOCOL={proto}"], exec_start="/usr/bin/tezos-accuser-start",
                            state_directory="tezos", user="tezos")),
        "tezos-endorser":
        ServiceFile(Unit(after=["network.target"], requires=[],
                        description="Tezos endorser"),
                    Service(environment_file=f"/etc/default/tezos-endorser-{proto}",
                            environment=[f"PROTOCOL=proto"], exec_start="/usr/bin/tezos-endorser-start",
                            state_directory="tezos", user="tezos")),
    }
    return services

def gen_service(service_name, proto="stub"):
    return gen_services(proto=proto)[service_name]

def print_service_file(service_file: ServiceFile, out):
    after = "".join(map(lambda x: f"After={x}\n", service_file.unit.after))
    requires = "".join(map(lambda x: f"Requires={x}\n", service_file.unit.requires))
    environment = "".join(map(lambda x: f"Environment=\"{x}\"\n", service_file.service.environment))
    file_contents = f'''# SPDX-FileCopyrightText: 2020 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: MPL-2.0
[Unit]
{after}{requires}Description={service_file.unit.description}
[Service]
EnvironmentFile={service_file.service.environment_file}
{environment}ExecStart={service_file.service.exec_start}
StateDirectory={service_file.service.state_directory}
User={service_file.service.user}
'''
    with open(out, 'w') as f:
        f.write(file_contents)
