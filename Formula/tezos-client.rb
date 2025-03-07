# SPDX-FileCopyrightText: 2021 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

class TezosClient < Formula
  @all_bins = []

  class << self
    attr_accessor :all_bins
  end
  homepage "https://gitlab.com/tezos/tezos"

  url "https://gitlab.com/tezos/tezos.git", :tag => "octez-v22.0-rc1", :shallow => false

  version "v22.0-rc1-1"

  build_dependencies = %w[pkg-config coreutils autoconf rsync wget rustup cmake opam opam]
  build_dependencies.each do |dependency|
    depends_on dependency => :build
  end

  dependencies = %w[gmp hidapi libev protobuf sqlite libpq tezos-sapling-params]
  dependencies.each do |dependency|
    depends_on dependency
  end
  desc "CLI client for interacting with tezos blockchain"

  bottle do
    root_url "https://github.com/serokell/tezos-packaging/releases/download/#{TezosClient.version}/"
    sha256 cellar: :any, ventura: "d78e123906418cf1ad4c162aa16480a7b3a4f2acbb6d661ab5673cb7117b52ed"
    sha256 cellar: :any, arm64_ventura: "f5577c29bded0196b20e8119fb42a9a836d9f44673ea3f69e3e5dac9c2f12b0e"
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
    install_template "src/bin_client/main_client.exe",
                     "_build/default/src/bin_client/main_client.exe",
                     "octez-client"
  end
end
