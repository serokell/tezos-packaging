# SPDX-FileCopyrightText: 2021 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

class TezosCodec < Formula
  @all_bins = []

  class << self
    attr_accessor :all_bins
  end
  homepage "https://gitlab.com/tezos/tezos"

  url "https://gitlab.com/tezos/tezos.git", :tag => "v12.2", :shallow => false

  version "v12.2-1"

  build_dependencies = %w[pkg-config autoconf rsync wget rustup-init]
  build_dependencies.each do |dependency|
    depends_on dependency => :build
  end

  dependencies = %w[gmp hidapi libev libffi]
  dependencies.each do |dependency|
    depends_on dependency
  end
  desc "A client to decode and encode JSON"

  bottle do
    root_url "https://github.com/serokell/tezos-packaging/releases/download/#{TezosCodec.version}/"
    sha256 cellar: :any, big_sur: "94c8c5cbe7ea7188b62cdb5bc43a45da8698b612a5cfc3a8e40e7ba10ec40e85"
    sha256 cellar: :any, arm64_big_sur: "430c33f2a9cfe7e3145fe42fa29c83ac5d21b6951617a9cd0cf4749abfa1a672"
    sha256 cellar: :any, catalina: "4b6b76fc8edec2c1ba773c075bae8852d940726c32f67397c696a8d15354b868"
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
    system "rustup-init", "--default-toolchain", "1.52.1", "-y"
    system "opam", "init", "--bare", "--debug", "--auto-setup", "--disable-sandboxing"
    system ["source .cargo/env",  "make build-deps"].join(" && ")
  end

  def install_template(dune_path, exec_path, name)
    bin.mkpath
    self.class.all_bins << name
    system ["eval $(opam env)", "dune build #{dune_path}", "cp #{exec_path} #{name}"].join(" && ")
    bin.install name
  end

  def install
    make_deps
    install_template "src/bin_codec/codec.exe",
                     "_build/default/src/bin_codec/codec.exe",
                     "tezos-codec"
  end
end
