# SPDX-FileCopyrightText: 2022 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

class TezosNodeGhostnet < Formula
  url "file:///dev/null"
  version "v20.0-beta2-1"

  depends_on "tezos-node"

  desc "Meta formula that provides background tezos-node service that runs on ghostnet"

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
                  --network=ghostnet \
                  "$@"
      else
          echo "Updating the node configuration..."
          "$node" config update \
                  --rpc-addr "$NODE_RPC_ADDR" \
                  --network=ghostnet \
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
    File.write("tezos-node-ghostnet-start", startup_contents)
    bin.install "tezos-node-ghostnet-start"
    print "Installing tezos-node-ghostnet service"
  end

  service do
    run opt_bin/"tezos-node-ghostnet-start"
    require_root true
    environment_variables TEZOS_CLIENT_DIR: var/"lib/tezos/client", NODE_RPC_ADDR: "127.0.0.1:8732", CERT_PATH: "", KEY_PATH: ""
    keep_alive true
    log_path var/"log/tezos-node-ghostnet.log"
    error_log_path var/"log/tezos-node-ghostnet.log"
  end

  def post_install
    mkdir_p "#{var}/lib/tezos/node-ghostnet"
    system "octez-node", "config", "init", "--data-dir" "#{var}/lib/tezos/node-ghostnet", "--network", "ghostnet"
  end
end
