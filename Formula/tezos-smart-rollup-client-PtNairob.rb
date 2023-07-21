#!/usr/bin/env ruby
# SPDX-FileCopyrightText: 2023 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

class TezosSmartRollupClientPtnairob < Formula
  @all_bins = []

  class << self
    attr_accessor :all_bins
  end
  homepage "https://gitlab.com/tezos/tezos"

  url "https://gitlab.com/tezos/tezos.git", :tag => "v17.2", :shallow => false

  version "v17.2-1"

  build_dependencies = %w[pkg-config coreutils autoconf rsync wget rustup-init cmake]
  build_dependencies.each do |dependency|
    depends_on dependency => :build
  end

  dependencies = %w[gmp hidapi libev libffi tezos-sapling-params]
  dependencies.each do |dependency|
    depends_on dependency
  end
  desc "Smart contract rollup CLI client for PtNairob"

  bottle do
    root_url "https://github.com/serokell/tezos-packaging/releases/download/#{TezosSmartRollupClientPtnairob.version}/"
    sha256 cellar: :any, big_sur: "0d6a8dba2b21a7f9a3768646ca1938133c51fb9bb1329b765a9c42ca268c673c"
    sha256 cellar: :any, arm64_big_sur: "94024f88559045386a02d57c60e32b526e4445824801d008c612147b6d606c0a"
    sha256 cellar: :any, monterey: "f63c58f0e6295ed5a948d4c767e4a7717ca0bf202e8322db80592ac1b4152a2e"
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
    install_template "src/proto_017_PtNairob/bin_sc_rollup_client/main_sc_rollup_client_017_PtNairob.exe",
                     "_build/default/src/proto_017_PtNairob/bin_sc_rollup_client/main_sc_rollup_client_017_PtNairob.exe",
                     "octez-smart-rollup-client-PtNairob"
  end
end
