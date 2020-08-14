# SPDX-FileCopyrightText: 2020 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: MPL-2.0

FROM ubuntu:18.04
RUN apt-get update && apt-get install -y libev-dev libgmp-dev libhidapi-dev m4 perl pkg-config \
  debhelper dh-make dh-systemd devscripts autotools-dev python3 python3-distutils wget
RUN apt-get install -y software-properties-common && add-apt-repository ppa:avsm/ppa && apt-get update && apt-get install -y opam
ENV USER dockerbuilder
RUN useradd dockerbuilder && mkdir /tezos-packaging
ENV HOME /tezos-packaging
COPY meta.json /tezos-packaging/meta.json
COPY protocols.json /tezos-packaging/protocols.json
WORKDIR /tezos-packaging/docker
ENV OPAMROOT "/tezos-packaging/docker/opamroot"
RUN opam init --bare --yes --disable-sandboxing
RUN opam switch create ocaml-base-compiler.4.09.1
RUN opam switch set ocaml-base-compiler.4.09.1
RUN opam install opam-bundle=0.4 --yes
WORKDIR /tezos-packaging/docker
COPY docker/package/package_generator.py /tezos-packaging/docker/package_generator.py
COPY docker/package/defaults /tezos-packaging/docker/defaults
COPY docker/package/scripts /tezos-packaging/docker/scripts
COPY docker/package/systemd /tezos-packaging/docker/systemd
ENTRYPOINT ["./package_generator.py"]
