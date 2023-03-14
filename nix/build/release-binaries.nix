# SPDX-FileCopyrightText: 2021 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

protocols:
let
  protocolsFormatted =
    builtins.concatStringsSep ", " (protocols.allowed ++ protocols.active);
in [
  {
    name = "octez-client";
    description = "CLI client for interacting with octez blockchain";
    supports = protocolsFormatted;
  }
  {
    name = "octez-admin-client";
    description = "Administration tool for the node";
    supports = protocolsFormatted;
  }
  {
    name = "octez-node";
    description =
      "Entry point for initializing, configuring and running a Octez node";
    supports = protocolsFormatted;
  }
  {
    name = "octez-signer";
    description = "A client to remotely sign operations or blocks";
    supports = protocolsFormatted;
  }
  {
    name = "octez-codec";
    description = "A client to decode and encode JSON";
    supports = protocolsFormatted;
  }
  {
    name = "octez-tx-rollup-node-PtLimaPt";
    description = "Transaction rollup node";
    supports = "PtLimaPt";
  }
  {
    name = "octez-tx-rollup-client-PtLimaPt";
    description = "Client for interacting with transaction rollup node";
    supports = "PtLimaPt";
  }
] ++ builtins.concatMap (protocol: [
  {
    name = "octez-baker-${protocol}";
    description = "Daemon for baking";
    supports = protocol;
  }
  {
    name = "octez-accuser-${protocol}";
    description = "Daemon for accusing";
    supports = protocol;
  }
]) protocols.active
