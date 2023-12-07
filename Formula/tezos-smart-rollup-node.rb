#!/usr/bin/env ruby

# SPDX-FileCopyrightText: 2023 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

class TezosSmartRollupNode < Formula
  @all_bins = []

  class << self
    attr_accessor :all_bins
  end
  homepage "https://gitlab.com/tezos/tezos"

  url "https://gitlab.com/tezos/tezos.git", :tag => "v19.0-rc1", :shallow => false

  version "v19.0-rc1-1"

  build_dependencies = %w[pkg-config coreutils autoconf rsync wget rustup-init cmake opam]
  build_dependencies.each do |dependency|
    depends_on dependency => :build
  end

  dependencies = %w[gmp hidapi libev libffi tezos-sapling-params]
  dependencies.each do |dependency|
    depends_on dependency
  end
  desc "Tezos smart contract rollup node"

  bottle do
    root_url "https://github.com/serokell/tezos-packaging/releases/download/#{TezosSmartRollupNode.version}/"
    sha256 cellar: :any, monterey: "ed0cb153141fd61d90070aa17b957a7dd62e47e2eb7aae6bc86ff1383c3204b7"
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
    # Here is the workaround to use opam 2.0.9 because Tezos is currently not compatible with opam 2.1.0 and newer
    arch = RUBY_PLATFORM.include?("arm64") ? "arm64" : "x86_64"
    system "rustup-init", "--default-toolchain", "1.71.1", "-y"
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
