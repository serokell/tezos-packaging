#!/usr/bin/env ruby

# SPDX-FileCopyrightText: 2023 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

class TezosSmartRollupNodePtnairob < Formula
  @all_bins = []

  class << self
    attr_accessor :all_bins
  end
  homepage "https://gitlab.com/tezos/tezos"

  url "https://gitlab.com/tezos/tezos.git", :tag => "v18.0", :shallow => false

  version "v18.0-1"

  build_dependencies = %w[pkg-config coreutils autoconf rsync wget rustup-init cmake opam]
  build_dependencies.each do |dependency|
    depends_on dependency => :build
  end

  dependencies = %w[gmp hidapi libev libffi tezos-sapling-params]
  dependencies.each do |dependency|
    depends_on dependency
  end
  desc "Tezos smart contract rollup node for PtNairob"

  bottle do
    root_url "https://github.com/serokell/tezos-packaging/releases/download/#{TezosSmartRollupNodePtnairob.version}/"
    sha256 cellar: :any, arm64_big_sur: "f27e60aa3b87d6964edd94639a43458902c3cc7e85de61a1c699f9511f036a19"
    sha256 cellar: :any, big_sur: "51625fa9cf14ec5db183043ea341ff9ddfeb5b888e6f357aa0ab3c21de59e6eb"
    sha256 cellar: :any, monterey: "407e53271e81773c3c0f8023eafd8e62eae4edf524eb1cfa294aa384c4de4dfe"
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
    system "rustup-init", "--default-toolchain", "1.64.0", "-y"
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

      node="#{bin}/octez-smart-rollup-node-PtNairob"

      "$node" init "$ROLLUP_MODE" config \
          for "$ROLLUP_ALIAS" \
          --rpc-addr "$ROLLUP_NODE_RPC_ENDPOINT" \
          --force

      "$node" --endpoint "$NODE_RPC_SCHEME://$NODE_RPC_ADDR" \
          run "$ROLLUP_MODE" for "$ROLLUP_ALIAS"
      EOS
    File.write("tezos-smart-rollup-node-PtNairob-start", startup_contents)
    bin.install "tezos-smart-rollup-node-PtNairob-start"
    make_deps
    install_template "src/proto_017_PtNairob/bin_sc_rollup_node/main_sc_rollup_node_017_PtNairob.exe",
                     "_build/default/src/proto_017_PtNairob/bin_sc_rollup_node/main_sc_rollup_node_017_PtNairob.exe",
                     "octez-smart-rollup-node-PtNairob"
  end

  service do
    run opt_bin/"tezos-smart-rollup-node-PtNairob-start"
    require_root true
    environment_variables TEZOS_CLIENT_DIR: var/"lib/tezos/client", NODE_RPC_ENDPOINT: "http://localhost:8732", ROLLUP_NODE_RPC_ENDPOINT: "127.0.0.1:8472", ROLLUP_MODE: "observer", ROLLUP_ALIAS: "rollup"
    keep_alive true
    log_path var/"log/tezos-smart-rollup-node-PtNairob.log"
    error_log_path var/"log/tezos-smart-rollup-node-PtNairob.log"
  end

  def post_install
    mkdir "#{var}/lib/tezos/client"
  end
end
