# SPDX-FileCopyrightText: 2020 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ
# Docker image from Tezos CI which already has all the dependencies
FROM registry.gitlab.com/tezos/opam-repository:runtime-build-test-dependencies--552c0009110429e5adfd093122ce4eaf6c8b10c2
RUN sudo apk --no-cache --virtual add unzip wget eudev-dev autoconf automake libtool linux-headers binutils
COPY ./build/build-libusb-and-hidapi.sh /build-libusb-and-hidapi.sh
RUN sudo /build-libusb-and-hidapi.sh
COPY ./build/static_libs.patch /home/tezos/static.patch
ARG TEZOS_VERSION
COPY ./build/build-tezos.sh /build-tezos.sh
RUN /build-tezos.sh ${TEZOS_VERSION}
