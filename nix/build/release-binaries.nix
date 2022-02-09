# SPDX-FileCopyrightText: 2019 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ
protocols:
let
  protocolsFormatted =
    builtins.concatStringsSep ", " (protocols.allowed ++ protocols.active);
  protocolsWithEndorser =
    builtins.filter (x: !(builtins.elem x protocols.active_noendorser)) protocols.active;
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
  {
    name = "tezos-sandbox";
    description = "A tool for setting up and running testing scenarios with the local blockchain";
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
]) protocols.active ++ builtins.concatMap (protocol: [
  {
    name = "tezos-endorser-${protocol}";
    description = "Daemon for endorsing";
    supports = protocol;
  }
]) protocolsWithEndorser
