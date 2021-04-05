# SPDX-FileCopyrightText: 2021 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ

class TezosBaker008Ptedo2zk < Formula
  @all_bins = []

  class << self
    attr_accessor :all_bins
  end
  homepage "https://gitlab.com/tezos/tezos"

  url "https://gitlab.com/tezos/tezos.git", :tag => "v9.0-rc1", :shallow => false

  version "v9.0-rc1-1"

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
    root_url "https://github.com/serokell/tezos-packaging/releases/download/#{TezosBaker008Ptedo2zk.version}/"
    sha256 "4adfe12e7463f9172bd7d608ed82fc71f4bfa50c32b33796d213f5ec8bf90da3" => :mojave
    sha256 "95f75861ae641bd5790724f9e22591fa6f2428ca600a3385ab25a9367bbd249b" => :catalina
    cellar :any
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

      baker="#{bin}/tezos-baker-008-PtEdo2Zk"

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
    File.write("tezos-baker-008-PtEdo2Zk-start", startup_contents)
    bin.install "tezos-baker-008-PtEdo2Zk-start"
    make_deps
    install_template "src/proto_008_PtEdo2Zk/bin_baker/main_baker_008_PtEdo2Zk.exe",
                     "_build/default/src/proto_008_PtEdo2Zk/bin_baker/main_baker_008_PtEdo2Zk.exe",
                     "tezos-baker-008-PtEdo2Zk"
  end
  plist_options manual: "tezos-baker-008-PtEdo2Zk run with local node"
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
          <string>#{opt_bin}/tezos-baker-008-PtEdo2Zk-start</string>
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
