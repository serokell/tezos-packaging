# SPDX-FileCopyrightText: 2021 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ

class TezosEndorser008Ptedo2zk < Formula
  @all_bins = []

  class << self
    attr_accessor :all_bins
  end
  homepage "https://gitlab.com/tezos/tezos"

  url "https://gitlab.com/tezos/tezos.git", :tag => "v9.1", :shallow => false

  version "v9.1-1"

  build_dependencies = %w[pkg-config autoconf rsync wget opam rustup-init]
  build_dependencies.each do |dependency|
    depends_on dependency => :build
  end

  dependencies = %w[gmp hidapi libev libffi]
  dependencies.each do |dependency|
    depends_on dependency
  end

  desc "Daemon for endorsing"

  bottle do
    root_url "https://github.com/serokell/tezos-packaging/releases/download/#{TezosEndorser008Ptedo2zk.version}/"
    sha256 cellar: :any, mojave: "897ae817057dc3f7e66d80b6378ddc7b8becb99877e4064cf48ba7649d0d2ac2"
    sha256 cellar: :any, catalina: "2b42134dd6ec6a1dcfad27d9584cb3b82a8788c4a1171d88f630d80707cef04e"
  end

  def make_deps
    ENV.deparallelize
    ENV["CARGO_HOME"]="./.cargo"
    system "rustup-init", "--default-toolchain", "1.44.0", "-y"
    system "opam", "init", "--bare", "--debug", "--auto-setup", "--disable-sandboxing"
    system ["source .cargo/env",  "make build-deps"].join(" && ")
  end

  def install_template(dune_path, exec_path, name)
    bin.mkpath
    self.class.all_bins << name
    system ["eval $(opam env)", "dune build #{dune_path}", "cp #{exec_path} #{name}"].join(" && ")
    bin.install name
  end


  def install
    startup_contents =
      <<~EOS
      #!/usr/bin/env bash

      set -euo pipefail

      endorser="#{bin}/tezos-endorser-008-PtEdo2Zk"

      endorser_dir="$DATA_DIR"

      endorser_config="$endorser_dir/config"
      mkdir -p "$endorser_dir"

      if [ ! -f "$endorser_config" ]; then
          "$endorser" --base-dir "$endorser_dir" \
                      --endpoint "$NODE_RPC_ENDPOINT" \
                      config init --output "$endorser_config" >/dev/null 2>&1
      else
          "$endorser" --base-dir "$endorser_dir" \
                      --endpoint "$NODE_RPC_ENDPOINT" \
                      config update >/dev/null 2>&1
      fi

      launch_endorser() {
          exec "$endorser" --base-dir "$endorser_dir" \
              --endpoint "$NODE_RPC_ENDPOINT" \
              run "$@"
      }

      if [[ -z "$ENDORSER_ACCOUNT" ]]; then
          launch_endorser
      else
          launch_endorser "$ENDORSER_ACCOUNT"
      fi
    EOS
    File.write("tezos-endorser-008-PtEdo2Zk-start", startup_contents)
    bin.install "tezos-endorser-008-PtEdo2Zk-start"
    make_deps
    install_template "src/proto_008_PtEdo2Zk/bin_endorser/main_endorser_008_PtEdo2Zk.exe",
                     "_build/default/src/proto_008_PtEdo2Zk/bin_endorser/main_endorser_008_PtEdo2Zk.exe",
                     "tezos-endorser-008-PtEdo2Zk"
  end

  plist_options manual: "tezos-endorser-008-PtEdo2Zk run"
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
          <string>#{opt_bin}/tezos-endorser-008-PtEdo2Zk-start</string>
          <key>EnvironmentVariables</key>
            <dict>
              <key>DATA_DIR</key>
              <string>#{var}/lib/tezos/client</string>
              <key>NODE_RPC_ENDPOINT</key>
              <string>http://localhost:8732</string>
              <key>ENDORSER_ACCOUNT</key>
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
    mkdir "#{var}/lib/tezos/client"
  end
end
