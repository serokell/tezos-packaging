# SPDX-FileCopyrightText: 2021 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

class TezosSigner < Formula
  @all_bins = []

  class << self
    attr_accessor :all_bins
  end
  homepage "https://gitlab.com/tezos/tezos"

  url "https://gitlab.com/tezos/tezos.git", :tag => "octez-v22.0-rc1", :shallow => false

  version "v22.0-rc1-1"

  build_dependencies = %w[pkg-config coreutils autoconf rsync wget rustup cmake opam]
  build_dependencies.each do |dependency|
    depends_on dependency => :build
  end

  dependencies = %w[gmp hidapi libev protobuf sqlite libpq]
  dependencies.each do |dependency|
    depends_on dependency
  end
  desc "A client to remotely sign operations or blocks"

  bottle do
    root_url "https://github.com/serokell/tezos-packaging/releases/download/#{TezosSigner.version}/"
    sha256 cellar: :any, ventura: "94ad878c05be9bf78ae33b09efb7713e01138448150ddcac80e083f0418e57a8"
    sha256 cellar: :any, arm64_ventura: "d8990e93dc69b4ed2cbf777bcddf0c13d2308cec31964a33821da0468b5d6e88"
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
    make_deps
    install_template "src/bin_signer/main_signer.exe",
                     "_build/default/src/bin_signer/main_signer.exe",
                     "octez-signer"
  end
end
