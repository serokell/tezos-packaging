<!--
   - SPDX-FileCopyrightText: 2019 TQ Tezos <https://tqtezos.com/>
   -
   - SPDX-License-Identifier: MPL-2.0
   -->

# Building and packaging tezos using docker

The following scripts can be used with `podman` instead of `docker`
as a virtualisation engine. In order to use `podman` you should
set environment variable `USE_PODMAN="True"`.

## Statically built binaries

Static binaries building using custom alpine image.

[`docker-static-build.sh`](docker-static-build.sh) will build tezos binaries
image defined in [Dockerfile](build/Dockerfile). In order to build them you should specify
`TEZOS_VERSION` env variable and run the script:
```
export TEZOS_VERSION="v7.3"
./docker-static-build.sh
```
After that, directory will contain built static binaries.

This script can optionally accept argument to define resulting binaries target architecture.
Currently supported architectures are: `host` and `aarch64`, so that
one can build native binaries for current architecture or build `aarch64` binaries on
`x86_64` machine.

### Compiling for `aarch64` on `x86_64` prerequisites

Docker image defined in [`Dockerfile.aarch64`](build/Dockerfile.aarch64) uses qemu for
compilation on `aarch64`. In particular it uses `qemu-aarch64-static` binary from
[qemu-user-static repo](https://github.com/multiarch/qemu-user-static/).
In order to be able to compile tezos using `aarch64` emulator you'll need to run:
```
docker run --rm --privileged multiarch/qemu-user-static:register --reset
```
This command will register qemu emulator in `binfmt_misc`.

Once this is done you should run the following command to build `aarch64` static tezos binaries:
```
./docker-static-build.sh aarch64
```

## Ubuntu packages

We provide a way to build both binary and source native Ubuntu packages.

[`docker-ubuntu-packages.sh`](docker-ubuntu-packages.sh) will build source or binary
packages depending on the passed argument (`source` and `binary` respectively).
This script builds packages inside docker image defined in [Dockerfile](package/Dockerfile).
This script uses [python script](package/package_generator.py) which generates meta information for
tezos packages based on information defined in [meta.json](../meta.json) and current tezos
version defined in [sources.json](../nix/nix/sources.json) and build native ubuntu packages.

### `.deb` packages

In order to build binary `.deb` packages specify `TEZOS_VERSION` and
run the following command:
```
export TEZOS_VERSION="v7.3"
cd .. && ./docker/docker-ubuntu-packages.sh binary
```

It is also possible to build single package. In order to do that run the following:
```
# cd .. && ./docker/docker-ubuntu-packages.sh binary <tezos-binary-name>
# Example for baker
export TEZOS_VERSION="v7.3"
cd .. && ./docker/docker-ubuntu-packages.sh binary tezos-baker-006-PsCARTHA
```

The build can take some time due to the fact that we build tezos and its dependencies
from scratch for each package individually.

Once the build is completed the packages will be located in `../out` directory.

In order to install `.deb` package run the following command:
```
sudo apt install <path to deb file>
```

### Source packages and publishing them on Launchpad PPA

In order to build source packages run the following commands:
```
export TEZOS_VERSION="v7.3"
cd .. && ./docker/docker-ubuntu-packages.sh source
# you can also build single source package
cd .. && ./docker/docker-ubuntu-packages.sh source tezos-baker-006-PsCARTHA
```

Once the packages build is complete `../out` directory will contain files required
for submitting packages to the Launchpad.

There are 5 files for each package: `.orig.tar.gz`, `.debian.tar.xz`,
`.dsc`, `.build-info`, `.changes`.

You can test source package building using [`pbuilder`](https://wiki.ubuntu.com/PbuilderHowto).

In order to push the packages to the Launchpad PPA `*.changes` files should should be updated with
the submitter info and signed.

In order to update `*.changes` files with the proper signer info run the following:
```
sed -i 's/^Changed-By: .*$/Changed-By: $signer_info/' ../out/*.changes
```

For example, `signer_info` can be the following: `Roman Melnikov <roman.melnikov@serokell.io>`

Once these files are updated, they should be signed using `debsign`.
```
debsign ../out/*.changes
```

Signed files now can be submitted to Launchpad PPA. In order to do that run the following
command for each `.changes` file:
```
dput ppa:serokell/tezos ../out/<package>.changes
```
