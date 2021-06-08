# SPDX-FileCopyrightText: 2021 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ

class TezosBaker009Psfloren < Formula
  @all_bins = []

  class << self
    attr_accessor :all_bins
  end
  homepage "https://gitlab.com/tezos/tezos"

  url "https://gitlab.com/tezos/tezos.git", :tag => "v9.2", :shallow => false

  version "v9.2-1"

  build_dependencies = %w[pkg-config autoconf rsync wget opam rustup-init]
  build_dependencies.each do |dependency|
    depends_on dependency => :build
  end

  dependencies = %w[gmp hidapi libev libffi tezos-sapling-params]
  dependencies.each do |dependency|
    depends_on dependency
  end
  desc "Daemon for baking"

  bottle do
    root_url "https://github.com/serokell/tezos-packaging/releases/download/#{TezosBaker009Psfloren.version}/"
    sha256 cellar: :any, mojave: "9fc313190e500ce7440d1b69037a4684dc3dd8ddfdbd04395ef02334fafd77bb"
    sha256 cellar: :any, catalina: "6d24fa54ddcc2e95edc0bc35810e98aacc3fd015cc29d6dd40e3a376f3a0af00"
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

      baker="#{bin}/tezos-baker-009-PsFLoren"

      baker_dir="$DATA_DIR"

      baker_config="$baker_dir/config"
      mkdir -p "$baker_dir"

      if [ ! -f "$baker_config" ]; then
          "$baker" --base-dir "$baker_dir" \
                  --endpoint "$NODE_RPC_ENDPOINT" \
                  config init --output "$baker_config" >/dev/null 2>&1
      else
          "$baker" --base-dir "$baker_dir" \
                  --endpoint "$NODE_RPC_ENDPOINT" \
                  config update >/dev/null 2>&1
      fi

      launch_baker() {
          exec "$baker" \
              --base-dir "$baker_dir" --endpoint "$NODE_RPC_ENDPOINT" \
              run with local node "$NODE_DATA_DIR" "$@"
      }

      if [[ -z "$BAKER_ACCOUNT" ]]; then
          launch_baker
      else
          launch_baker "$BAKER_ACCOUNT"
      fi
    EOS
    File.write("tezos-baker-009-PsFLoren-start", startup_contents)
    bin.install "tezos-baker-009-PsFLoren-start"
    make_deps
    install_template "src/proto_009_PsFLoren/bin_baker/main_baker_009_PsFLoren.exe",
                     "_build/default/src/proto_009_PsFLoren/bin_baker/main_baker_009_PsFLoren.exe",
                     "tezos-baker-009-PsFLoren"
  end
  plist_options manual: "tezos-baker-009-PsFLoren run with local node"
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
          <string>#{opt_bin}/tezos-baker-009-PsFLoren-start</string>
          <key>EnvironmentVariables</key>
            <dict>
              <key>DATA_DIR</key>
              <string>#{var}/lib/tezos/client</string>
              <key>NODE_DATA_DIR</key>
              <string></string>
              <key>NODE_RPC_ENDPOINT</key>
              <string>http://localhost:8732</string>
              <key>BAKER_ACCOUNT</key>
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
