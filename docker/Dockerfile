# SPDX-FileCopyrightText: 2020 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: MPL-2.0

FROM alpine:3.11
RUN apk update
RUN apk --no-cache --virtual add rsync git m4 build-base patch unzip \
  bubblewrap wget pkgconfig gmp-dev libev-dev hidapi-dev eudev-dev perl opam libusb-dev bash \
  autoconf automake libtool linux-headers
RUN git clone --single-branch --branch v1.0.23 https://github.com/libusb/libusb.git --depth 1
RUN cd libusb && autoreconf -fvi && ./configure && make && make install
RUN git clone --single-branch --branch hidapi-0.9.0 https://github.com/libusb/hidapi.git --depth 1
RUN cd hidapi && autoreconf -fvi && ./bootstrap && ./configure && make && make install
RUN rm -rf libusb hidapi
COPY ./static_libs.patch /static.patch
RUN git clone --single-branch --branch v7.1 https://gitlab.com/tezos/tezos.git --depth 1
WORKDIR /tezos
RUN git apply ../static.patch
RUN export OPAMYES="true" && opam init --bare --disable-sandboxing && make build-deps
RUN eval "$(opam env)" && make
