# SPDX-FileCopyrightText: 2021 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

protocols:
let
  protocolsFormatted =
    builtins.concatStringsSep ", " (protocols.allowed ++ protocols.active);
in [
  {
    name = "tezos-client";
    description = "CLI client for interacting with tezos blockchain";
    supports = protocolsFormatted;
  }
  {
    name = "tezos-admin-client";
    description = "Administration tool for the node";
    supports = protocolsFormatted;
  }
  {
    name = "tezos-node";
    description =
      "Entry point for initializing, configuring and running a Tezos node";
    supports = protocolsFormatted;
  }
  {
    name = "tezos-signer";
    description = "A client to remotely sign operations or blocks";
    supports = protocolsFormatted;
  }
  {
    name = "tezos-codec";
    description = "A client to decode and encode JSON";
    supports = protocolsFormatted;
  }
] ++ builtins.concatMap (protocol: [
  {
    name = "tezos-baker-${protocol}";
    description = "Daemon for baking";
    supports = protocol;
  }
  {
    name = "tezos-accuser-${protocol}";
    description = "Daemon for accusing";
    supports = protocol;
  }
  {
    name = "tezos-tx-rollup-node-${protocol}";
    description = "Transaction rollup node";
    supports = protocol;
  }
  {
    name = "tezos-tx-rollup-client-${protocol}";
    description = "Client for interacting with transaction rollup node";
    supports = protocol;
  }
]) protocols.active
