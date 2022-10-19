# SPDX-FileCopyrightText: 2022 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

class TezosTxRollupClientPtkathma < Formula
  @all_bins = []

  class << self
    attr_accessor :all_bins
  end
  homepage "https://gitlab.com/tezos/tezos"

  url "https://gitlab.com/tezos/tezos.git", :tag => "v15.0-rc1", :shallow => false

  version "v15.0-rc1-1"

  build_dependencies = %w[pkg-config coreutils autoconf rsync wget rustup-init]
  build_dependencies.each do |dependency|
    depends_on dependency => :build
  end

  dependencies = %w[gmp hidapi libev libffi tezos-sapling-params]
  dependencies.each do |dependency|
    depends_on dependency
  end
  desc "Transaction rollup CLI client for PtKathma"

  bottle do
    root_url "https://github.com/serokell/tezos-packaging/releases/download/#{TezosTxRollupClientPtkathma.version}/"
    sha256 cellar: :any, monterey: "7d5de56fb74ea4702904af5ec43ceb995ac1717e8d1c35d52611b8591b8fadc8"
    sha256 cellar: :any, big_sur: "98a2e8cd1c9ffa9b259a29974e50defac3c08466b841eb10e3912fc06060d74e"
    sha256 cellar: :any, arm64_big_sur: "c79a6a95a703b8bf0df9dba66fc8ea1036c812e53b4cc31d5f64972972f87961"
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
    make_deps
    install_template "src/proto_014_PtKathma/bin_tx_rollup_client/main_tx_rollup_client_014_PtKathma.exe",
                     "_build/default/src/proto_014_PtKathma/bin_tx_rollup_client/main_tx_rollup_client_014_PtKathma.exe",
                     "octez-tx-rollup-client-PtKathma"
  end
end
