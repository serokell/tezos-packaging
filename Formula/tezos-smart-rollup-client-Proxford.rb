#!/usr/bin/env ruby
# SPDX-FileCopyrightText: 2023 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

class TezosSmartRollupClientProxford < Formula
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

  dependencies = %w[gmp hidapi libev tezos-sapling-params]
  dependencies.each do |dependency|
    depends_on dependency
  end
  desc "Smart contract rollup CLI client for Proxford"

  bottle do
    root_url "https://github.com/serokell/tezos-packaging/releases/download/#{TezosSmartRollupClientProxford.version}/"
    sha256 cellar: :any, arm64_big_sur: "496706f919534f9c4ea231c2d885cb5189170151776b22c4741be89cc3161a59"
    sha256 cellar: :any, big_sur: "20da81cd0f564c69e52c96524df6e1b09b970829a7f38d8fa7c29f570c7f58c6"
    sha256 cellar: :any, monterey: "b437b9110236f17afeebee95a3bd40ffd82a605f31e3b4c28338e39c0ee415ae"
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
    make_deps
    install_template "src/proto_018_Proxford/bin_sc_rollup_client/main_sc_rollup_client_018_Proxford.exe",
                     "_build/default/src/proto_018_Proxford/bin_sc_rollup_client/main_sc_rollup_client_018_Proxford.exe",
                     "octez-smart-rollup-client-Proxford"
  end
end
