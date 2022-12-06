# SPDX-FileCopyrightText: 2022 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

class TezosTxRollupClientPtlimapt < Formula
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
  desc "Transaction rollup CLI client for PtLimaPt"

  bottle do
    root_url "https://github.com/serokell/tezos-packaging/releases/download/#{TezosTxRollupClientPtlimapt.version}/"
    sha256 cellar: :any, monterey: "ff47a64f451727bf726a5c23d1717ad5999925f46e8adc4558982c55f467895f"
    sha256 cellar: :any, big_sur: "37776b0250a10cfcd9d28430deb79d27ee029bed383496e1a5d96e2d7f9b05f4"
    sha256 cellar: :any, arm64_big_sur: "492cfde845f4826df65a6bbdc7429fb1b59f0563b5e4bdf8f9eb23a409f0e434"
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
    install_template "src/proto_015_PtLimaPt/bin_tx_rollup_client/main_tx_rollup_client_015_PtLimaPt.exe",
                     "_build/default/src/proto_015_PtLimaPt/bin_tx_rollup_client/main_tx_rollup_client_015_PtLimaPt.exe",
                     "octez-tx-rollup-client-PtLimaPt"
  end
end
