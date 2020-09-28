#! /usr/bin/env python3

# SPDX-FileCopyrightText: 2020 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: MPL-2.0

import package.systemd_files_generator as gen
import sys

if len(sys.argv) > 1:
    service_name = sys.argv[1]
    if len(sys.argv) == 3:
        service_file = gen.gen_service(service_name, sys.argv[2])
    else:
        service_file = gen.gen_service(service_name)
    gen.print_service_file(service_file, f"{service_name}.service")
