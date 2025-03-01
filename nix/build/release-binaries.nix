# SPDX-FileCopyrightText: 2021 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

protocols:
let
  protocolsFormatted =
    builtins.concatStringsSep ", " (protocols.allowed ++ protocols.active);
in [
  {
    name = "octez-client";
    description = ''
      CLI client for interacting with octez blockchain and a basic wallet.
      For more information see - https://tezos.gitlab.io/introduction/howtouse.html#client
    '';
    supports = protocolsFormatted;
  }
  {
    name = "octez-admin-client";
    description = ''
      CLI administrator tool for peers management
      For more information please check - https://tezos.gitlab.io/user/various.html#octez-admin-client
    '';
    supports = protocolsFormatted;
  }
  {
    name = "octez-node";
    description = ''
      Entry point for initializing, configuring and running a Octez node
      For more information please check - https://tezos.gitlab.io/introduction/howtouse.html#node
    '';
    supports = protocolsFormatted;
  }
  {
    name = "octez-dal-node";
    description =''
      A Data Availability Layer Tezos node.
      For more info on DAL please check https://tezos.gitlab.io/shell/dal_overview.html
    '';
    supports = protocolsFormatted;
  }
  {
    name = "octez-signer";
    description = ''
      A client to remotely sign operations or blocks.
      For more info please check - https://tezos.gitlab.io/user/key-management.html#signer
    '';
    supports = protocolsFormatted;
  }
  {
    name = "octez-codec";
    description = ''
      A utility for documenting the data encodings and for performing data encoding/decoding.
      For more info please check - https://tezos.gitlab.io/introduction/howtouse.html#codec
    '';
    supports = protocolsFormatted;
  }
  {
    name = "octez-smart-rollup-wasm-debugger";
    description = ''
      Debugger for smart rollup kernels
      For more info please check - https://tezos.gitlab.io/active/smart_rollups.html
    '';
    supports = protocolsFormatted;
  }
  {
    name = "octez-smart-rollup-node";
    description = ''
      Tezos smart contract rollup node.
      For more info please check - https://tezos.gitlab.io/active/smart_rollups.html#tools
    '';
    supports = protocolsFormatted;
  }
] ++ builtins.concatMap (protocol: [
  {
    name = "octez-baker-${protocol}";
    description = ''
      Daemon for baking for ${protocol} protocol.
      For more info please check - https://tezos.gitlab.io/introduction/howtorun.html#baker
    '';
    supports = protocol;
  }
  {
    name = "octez-accuser-${protocol}";
    description = ''
      Daemon for accusing for ${protocol} protocol.
      For more info please check - https://tezos.gitlab.io/introduction/howtorun.html#accuser
    '';
    supports = protocol;
  }
]) protocols.active
