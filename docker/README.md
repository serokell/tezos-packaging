<!--
   - SPDX-FileCopyrightText: 2019 TQ Tezos <https://tqtezos.com/>
   -
   - SPDX-License-Identifier: MPL-2.0
   -->

# Building and packaging tezos using docker

## Statically built binaries

Static binaries building using custom alpine image.

[`docker-static-build.sh`](docker-static-build.sh) will build tezos binaries
image defined in [Dockerfile](build/Dockerfile). In order to build them, just run the script
```
./docker-static-build.sh
```
After that, directory will contain built static binaries.
