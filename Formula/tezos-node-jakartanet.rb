# SPDX-FileCopyrightText: 2022 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

class TezosNodeJakartanet < Formula
  url "file:///dev/null"
  version "v14.0-1"

  depends_on "tezos-node"

  desc "Meta formula that provides background tezos-node service that runs on jakartanet"

  def install
    startup_contents =
      <<~EOS
      #!/usr/bin/env bash

      set -euo pipefail

      node="/usr/local/bin/tezos-node"
      # default location of the config file
      config_file="$DATA_DIR/config.json"

      mkdir -p "$DATA_DIR"
      if [[ ! -f "$config_file" ]]; then
          echo "Configuring the node..."
          "$node" config init \
                  --data-dir "$DATA_DIR" \
                  --rpc-addr "$NODE_RPC_ADDR" \
                  --network=jakartanet \
                  "$@"
      else
          echo "Updating the node configuration..."
          "$node" config update \
                  --data-dir "$DATA_DIR" \
                  --rpc-addr "$NODE_RPC_ADDR" \
                  --network=jakartanet \
                  "$@"
      fi

      # Launching the node
      if [[ -z "$CERT_PATH" || -z "$KEY_PATH" ]]; then
          exec "$node" run --data-dir "$DATA_DIR" --config-file="$config_file"
      else
          exec "$node" run --data-dir "$DATA_DIR" --config-file="$config_file" \
              --rpc-tls="$CERT_PATH","$KEY_PATH"
      fi
    EOS
    File.write("tezos-node-jakartanet-start", startup_contents)
    bin.install "tezos-node-jakartanet-start"
    print "Installing tezos-node-jakartanet service"
  end
  def plist
    <<~EOS
      <?xml version="1.0" encoding="UTF-8"?>
      <!DOCTYPE plist PUBLIC "-//Apple Computer//DTD PLIST 1.0//EN"
      "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
      <plist version="1.0">
        <dict>
          <key>Label</key>
          <string>#{plist_name}</string>
          <key>Program</key>
          <string>#{opt_bin}/tezos-node-jakartanet-start</string>
          <key>EnvironmentVariables</key>
            <dict>
              <key>DATA_DIR</key>
              <string>#{var}/lib/tezos/node-jakartanet</string>
              <key>NODE_RPC_ADDR</key>
              <string>127.0.0.1:8732</string>
              <key>CERT_PATH</key>
              <string></string>
              <key>KEY_PATH</key>
              <string></string>
          </dict>
          <key>RunAtLoad</key><true/>
          <key>StandardOutPath</key>
          <string>#{var}/log/#{name}.log</string>
          <key>StandardErrorPath</key>
          <string>#{var}/log/#{name}.log</string>
        </dict>
      </plist>
    EOS
  end
  def post_install
    mkdir_p "#{var}/lib/tezos/node-jakartanet"
    system "tezos-node", "config", "init", "--data-dir" "#{var}/lib/tezos/node-jakartanet", "--network", "jakartanet"
  end
end
