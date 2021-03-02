# SPDX-FileCopyrightText: 2021 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ

class TezosNodeEdo2net < Formula
  url "file:///dev/null"
  version "v8.2-3"

  bottle :unneeded
  depends_on "tezos-node"

  desc "Meta formula that provides backround tezos-node service that runs on edo2net"

  @@edo2net_config =
      <<~EOS
{
"p2p": {},
"network":
    { "genesis":
        { "timestamp": "2021-02-11T14:00:00Z",
          "block": "BLockGenesisGenesisGenesisGenesisGenesisdae8bZxCCxh",
          "protocol": "PtYuensgYBb3G3x1hLLbCmcav8ue8Kyd2khADcL5LsT5R1hcXex" },
      "genesis_parameters":
        { "values":
            { "genesis_pubkey":
                "edpkugeDwmwuwyyD3Q5enapgEYDxZLtEUFFSrvVwXASQMVEqsvTqWu" } },
      "chain_name": "TEZOS_EDO2NET_2021-02-11T14:00:00Z",
      "sandboxed_chain_name": "SANDBOXED_TEZOS",
      "default_bootstrap_peers":
        [ "edonet.tezos.co.il", "188.40.128.216:29732", "edo2net.kaml.fr",
          "edonet2.smartpy.io", "51.79.165.131", "edonetb.boot.tezostaquito.io" ] }
}
  EOS
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
          cat > "$config_file" <<-EOM
      #{@@edo2net_config}
      EOM
          "$node" config update \
                  --data-dir "$DATA_DIR" \
                  --rpc-addr "$NODE_RPC_ADDR" \
                  "$@"
      else
          echo "Updating the node configuration..."
          "$node" config update \
                  --data-dir "$DATA_DIR" \
                  --rpc-addr "$NODE_RPC_ADDR" \
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
    File.write("tezos-node-edo2net-start", startup_contents)
    bin.install "tezos-node-edo2net-start"
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
          <string>#{opt_bin}/tezos-node-edo2net-start</string>
          <key>EnvironmentVariables</key>
            <dict>
              <key>DATA_DIR</key>
              <string>#{var}/lib/tezos/node-edo2net</string>
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
    mkdir "#{var}/lib/tezos/node-edo2net"
    File.write("#{var}/lib/tezos/node-edo2net/config.json", @@edo2net_config)
  end
end
