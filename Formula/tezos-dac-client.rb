# SPDX-FileCopyrightText: 2021 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

class TezosDacClient < Formula
  @all_bins = []

  class << self
    attr_accessor :all_bins
  end
  homepage "https://gitlab.com/tezos/tezos"

  url "https://gitlab.com/tezos/tezos.git", :tag => "v18.1", :shallow => false

  version "v18.1-1"

  build_dependencies = %w[pkg-config coreutils autoconf rsync wget rustup-init cmake opam]
  build_dependencies.each do |dependency|
    depends_on dependency => :build
  end

  dependencies = %w[gmp hidapi libev tezos-sapling-params]
  dependencies.each do |dependency|
    depends_on dependency
  end
  desc "A Data Availability Committee Tezos client"

  bottle do
    root_url "https://github.com/serokell/tezos-packaging/releases/download/#{TezosDacClient.version}/"
    sha256 cellar: :any, big_sur: "c08f4f6d0df58951d894c2b19dc9c60b5c56c9d5bed6c0e9dd8967a97ab0089a"
    sha256 cellar: :any, arm64_big_sur: "a859f17b146f8e8a50ef0d43cb0b1fcf85aa24dc75ddaddd1ca49ddcf997643a"
    sha256 cellar: :any, monterey: "e3fd536dd16b972d495e2e32435dd7abb12eb154864f3ec458c73860d009fa74"
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
    install_template "src/bin_dac_client/main_dac_client.exe",
                     "_build/default/src/bin_dac_client/main_dac_client.exe",
                     "octez-dac-client"
  end
end
