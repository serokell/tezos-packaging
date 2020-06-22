# SPDX-FileCopyrightText: 2019 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: MPL-2.0

let
  protocols = import ../protocols.nix;
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
    name = "tezos-endorser-${protocol}";
    description = "Daemon for endorsing";
    supports = protocol;
  }
]) protocols.active
