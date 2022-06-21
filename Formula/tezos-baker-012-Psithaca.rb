# SPDX-FileCopyrightText: 2022 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

class TezosBaker012Psithaca < Formula
  @all_bins = []

  class << self
    attr_accessor :all_bins
  end
  homepage "https://gitlab.com/tezos/tezos"

  url "https://gitlab.com/tezos/tezos.git", :tag => "v13.0", :shallow => false

  version "v13.0-1"

  build_dependencies = %w[pkg-config autoconf rsync wget rustup-init]
  build_dependencies.each do |dependency|
    depends_on dependency => :build
  end

  dependencies = %w[gmp hidapi libev libffi tezos-sapling-params]
  dependencies.each do |dependency|
    depends_on dependency
  end
  desc "Daemon for baking"

  bottle do
    root_url "https://github.com/serokell/tezos-packaging/releases/download/#{TezosBaker012Psithaca.version}/"
    sha256 cellar: :any, catalina: "690bdec90eb45090d4e1c0a13f3c289dca5a5445fd124fd7703b61976b05938c"
    sha256 cellar: :any, big_sur: "86d3a0576187994ff33869cd6406972d219b762cd07dd160928d42451d5ac918"
    sha256 cellar: :any, arm64_big_sur: "2629578fe67caed75f93cb025f63a251de5c1fc3eae7240b030c97f52ed4ff13"
    sha256 cellar: :any, catalina: "690bdec90eb45090d4e1c0a13f3c289dca5a5445fd124fd7703b61976b05938c"
  end

  def make_deps
    ENV.deparallelize
    ENV["CARGO_HOME"]="./.cargo"
    # Disable usage of instructions from the ADX extension to avoid incompatibility
    # with old CPUs, see https://gitlab.com/dannywillems/ocaml-bls12-381/-/merge_requests/135/
    ENV["BLST_PORTABLE"]="yes"
    # Here is the workaround to use opam 2.0.9 because Tezos is currently not compatible with opam 2.1.0 and newer
    arch = RUBY_PLATFORM.include?("arm64") ? "arm64" : "x86_64"
    system "curl", "-L", "https://github.com/ocaml/opam/releases/download/2.0.9/opam-2.0.9-#{arch}-macos", "--create-dirs", "-o", "#{ENV["HOME"]}/.opam-bin/opam"
    system "chmod", "+x", "#{ENV["HOME"]}/.opam-bin/opam"
    ENV["PATH"]="#{ENV["HOME"]}/.opam-bin:#{ENV["PATH"]}"
    system "rustup-init", "--default-toolchain", "1.52.1", "-y"
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

      baker="#{bin}/tezos-baker-012-Psithaca"

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
    File.write("tezos-baker-012-Psithaca-start", startup_contents)
    bin.install "tezos-baker-012-Psithaca-start"
    make_deps
    install_template "src/proto_012_Psithaca/bin_baker/main_baker_012_Psithaca.exe",
                     "_build/default/src/proto_012_Psithaca/bin_baker/main_baker_012_Psithaca.exe",
                     "tezos-baker-012-Psithaca"
  end
  plist_options manual: "tezos-baker-012-Psithaca run with local node"
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
          <string>#{opt_bin}/tezos-baker-012-Psithaca-start</string>
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
