# SPDX-FileCopyrightText: 2019 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: MPL-2.0

let
  protocols = import ./protocols.nix;
  protocolsFormatted = builtins.concatStringsSep ", " (protocols.allowed ++ protocols.active);
in[
  {
    name = "tezos-client";
    description = "CLI client for interacting with tezos blockchain. Supports ${protocolsFormatted}";
  }
  {
    name = "tezos-node";
    description =
      "Entry point for initializing, configuring and running a Tezos node. Supports ${protocolsFormatted}";
  }
  {
    name = "tezos-signer";
    description = "A client to remotely sign operations or blocks. Supports ${protocolsFormatted}";
  }
] ++ builtins.concatMap (protocol: [
  {
    name = "tezos-baker-${protocol}";
    description = "Daemon for baking (protocol: ${protocol})";
  }
  {
    name = "tezos-accuser-${protocol}";
    description = "Daemon for accusing (protocol: ${protocol})";
  }
  {
    name = "tezos-endorser-${protocol}";
    description = "Daemon for endorsing (protocol: ${protocol})";
  }
]) protocols.active
