#!/usr/bin/env ruby

# SPDX-FileCopyrightText: 2023 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

class TezosSmartRollupNode < Formula
  @all_bins = []

  class << self
    attr_accessor :all_bins
  end
  homepage "https://gitlab.com/tezos/tezos"

  url "https://gitlab.com/tezos/tezos.git", :tag => "octez-v21.2", :shallow => false

  version "v21.2-1"

  build_dependencies = %w[pkg-config coreutils autoconf rsync wget rustup cmake opam]
  build_dependencies.each do |dependency|
    depends_on dependency => :build
  end

  dependencies = %w[gmp hidapi libev protobuf sqlite libpq libffi tezos-sapling-params]
  dependencies.each do |dependency|
    depends_on dependency
  end
  desc "Tezos smart contract rollup node"

  bottle do
    root_url "https://github.com/serokell/tezos-packaging/releases/download/#{TezosSmartRollupNode.version}/"
    sha256 cellar: :any, arm64_ventura: "f187681f00e4f7693445526921d04dade11a74172fc77959d4d15d7d975f2406"
    sha256 cellar: :any, ventura: "e333ea264ca642a81b464331d09e01b0b140deaa39811b7802f47cbde021b842"
  end

  def make_deps
    ENV.deparallelize
    ENV["CARGO_HOME"]="./.cargo"
    # Disable usage of instructions from the ADX extension to avoid incompatibility
    # with old CPUs, see https://gitlab.com/dannywillems/ocaml-bls12-381/-/merge_requests/135/
    ENV["BLST_PORTABLE"]="yes"
    # Force linker to use libraries from the current brew installation.
    # Workaround for https://github.com/serokell/tezos-packaging/issues/700
    ENV["LDFLAGS"] = "-L#{HOMEBREW_PREFIX}/lib"
    # Workaround to avoid linking problem on mac
    ENV["RUSTFLAGS"]= "-C link-args=-Wl,-undefined,dynamic_lookup"
    # Here is the workaround to use opam 2.0.9 because Tezos is currently not compatible with opam 2.1.0 and newer
    arch = RUBY_PLATFORM.include?("arm64") ? "arm64" : "x86_64"
    system "rustup", "install", "1.78.0"
    system "opam", "init", "--bare", "--debug", "--auto-setup", "--disable-sandboxing"
    system "make build-deps"
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

      node="#{bin}/octez-smart-rollup-node"

      "$node" init "$ROLLUP_MODE" config \
          for "$ROLLUP_ALIAS" \
          --rpc-addr "$ROLLUP_NODE_RPC_ENDPOINT" \
          --force

      "$node" --endpoint "$NODE_RPC_SCHEME://$NODE_RPC_ADDR" \
          run "$ROLLUP_MODE" for "$ROLLUP_ALIAS"
      EOS
    File.write("tezos-smart-rollup-node-start", startup_contents)
    bin.install "tezos-smart-rollup-node-start"
    make_deps
    install_template "src/bin_smart_rollup_node/main_smart_rollup_node.exe",
                     "_build/default/src/bin_smart_rollup_node/main_smart_rollup_node.exe",
                     "octez-smart-rollup-node"
  end

  service do
    run opt_bin/"tezos-smart-rollup-node-start"
    require_root true
    environment_variables TEZOS_CLIENT_DIR: var/"lib/tezos/client", NODE_RPC_ENDPOINT: "http://localhost:8732", ROLLUP_NODE_RPC_ENDPOINT: "127.0.0.1:8472", ROLLUP_MODE: "observer", ROLLUP_ALIAS: "rollup"
    keep_alive true
    log_path var/"log/tezos-smart-rollup-node.log"
    error_log_path var/"log/tezos-smart-rollup-node.log"
  end

  def post_install
    mkdir "#{var}/lib/tezos/client"
  end
end
