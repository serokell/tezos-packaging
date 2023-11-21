# SPDX-FileCopyrightText: 2021 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

class TezosNodeMainnet < Formula
  url "file:///dev/null"
  version "v18.1-1"

  depends_on "tezos-node"

  desc "Meta formula that provides background tezos-node service that runs on mainnet"

  def install
    startup_contents =
      <<~EOS
      #!/usr/bin/env bash

      set -euo pipefail

      node="/usr/local/bin/octez-node"
      # default location of the config file
      config_file="$TEZOS_CLIENT_DIR/config.json"

      mkdir -p "$TEZOS_CLIENT_DIR"
      if [[ ! -f "$config_file" ]]; then
          echo "Configuring the node..."
          "$node" config init \
                  --rpc-addr "$NODE_RPC_ADDR" \
                  --network=mainnet \
                  "$@"
      else
          echo "Updating the node configuration..."
          "$node" config update \
                  --rpc-addr "$NODE_RPC_ADDR" \
                  --network=mainnet \
                  "$@"
      fi

      # Launching the node
      if [[ -z "$CERT_PATH" || -z "$KEY_PATH" ]]; then
          exec "$node" run --config-file="$config_file"
      else
          exec "$node" run --config-file="$config_file" \
              --rpc-tls="$CERT_PATH","$KEY_PATH"
      fi
    EOS
    File.write("tezos-node-mainnet-start", startup_contents)
    bin.install "tezos-node-mainnet-start"
    print "Installing tezos-node-mainnet service"
  end

  service do
    run opt_bin/"tezos-node-mainnet-start"
    require_root true
    environment_variables TEZOS_CLIENT_DIR: var/"lib/tezos/client", NODE_RPC_ADDR: "127.0.0.1:8732", CERT_PATH: "", KEY_PATH: ""
    keep_alive true
    log_path var/"log/tezos-node-mainnet.log"
    error_log_path var/"log/tezos-node-mainnet.log"
  end

  def post_install
    mkdir_p "#{var}/lib/tezos/node-mainnet"
    system "octez-node", "config", "init", "--data-dir" "#{var}/lib/tezos/node-mainnet", "--network", "mainnet"
  end
end
