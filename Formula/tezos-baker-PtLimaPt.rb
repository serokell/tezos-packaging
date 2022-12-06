# SPDX-FileCopyrightText: 2022 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

class TezosBakerPtlimapt < Formula
  @all_bins = []

  class << self
    attr_accessor :all_bins
  end
  homepage "https://gitlab.com/tezos/tezos"

  url "https://gitlab.com/tezos/tezos.git", :tag => "v15.1", :shallow => false

  version "v15.1-1"

  build_dependencies = %w[pkg-config coreutils autoconf rsync wget rustup-init]
  build_dependencies.each do |dependency|
    depends_on dependency => :build
  end

  dependencies = %w[gmp hidapi libev libffi tezos-sapling-params]
  dependencies.each do |dependency|
    depends_on dependency
  end
  desc "Daemon for baking"

  bottle do
    root_url "https://github.com/serokell/tezos-packaging/releases/download/#{TezosBakerPtlimapt.version}/"
    sha256 cellar: :any, monterey: "e3b27a0cc54399616d3bea79fb215df2f95a40e90a5cf804f747ccfe07cb5145"
    sha256 cellar: :any, big_sur: "19477e3350999cdddf00406705576da0441f6f4de8f6a778150fcc1aef3a787d"
    sha256 cellar: :any, arm64_big_sur: "488f2535633ac2fa5188be2aa88870673224d3aee3670f9a2da5731f6daf4d66"
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
    system "rustup-init", "--default-toolchain", "1.60.0", "-y"
    system "opam", "init", "--bare", "--debug", "--auto-setup", "--disable-sandboxing"
    system ["source .cargo/env",  "make build-deps"].join(" && ")
  end

  def install_template(dune_path, exec_path, name)
    bin.mkpath
    self.class.all_bins << name
    system ["eval $(opam env)", "dune build #{dune_path}", "cp #{exec_path} #{name}"].join(" && ")
    bin.install name
    ln_sf "#{bin}/#{name}", "#{bin}/#{name.gsub("octez", "tezos")}"
  end

  def install
    startup_contents =
      <<~EOS
      #!/usr/bin/env bash

      set -euo pipefail

      baker="#{bin}/octez-baker-PtLimaPt"

      baker_config="$TEZOS_CLIENT_DIR/config"
      mkdir -p "$TEZOS_CLIENT_DIR"

      if [ ! -f "$baker_config" ]; then
          "$baker" --endpoint "$NODE_RPC_SCHEME://$NODE_RPC_ADDR" \
                  config init --output "$baker_config" >/dev/null 2>&1
      else
          "$baker" --endpoint "$NODE_RPC_SCHEME://$NODE_RPC_ADDR" \
                  config update >/dev/null 2>&1
      fi

      launch_baker() {
          exec "$baker" \
              --endpoint "$NODE_RPC_SCHEME://$NODE_RPC_ADDR" \
              run with local node "$TEZOS_NODE_DIR" "$@"
      }

      if [[ -z "$BAKER_ACCOUNT" ]]; then
          launch_baker
      else
          launch_baker "$BAKER_ACCOUNT"
      fi
    EOS
    File.write("tezos-baker-PtLimaPt-start", startup_contents)
    bin.install "tezos-baker-PtLimaPt-start"
    make_deps
    install_template "src/proto_015_PtLimaPt/bin_baker/main_baker_015_PtLimaPt.exe",
                     "_build/default/src/proto_015_PtLimaPt/bin_baker/main_baker_015_PtLimaPt.exe",
                     "octez-baker-PtLimaPt"
  end
  plist_options manual: "tezos-baker-PtLimaPt run with local node"
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
          <string>#{opt_bin}/tezos-baker-PtLimaPt-start</string>
          <key>EnvironmentVariables</key>
            <dict>
              <key>TEZOS_CLIENT_DIR</key>
              <string>#{var}/lib/tezos/client</string>
              <key>TEZOS_NODE_DIR</key>
              <string></string>
              <key>NODE_RPC_SCHEME</key>
              <string>http</string>
              <key>NODE_RPC_ADDR</key>
              <string>localhost:8732</string>
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
