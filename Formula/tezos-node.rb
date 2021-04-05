# SPDX-FileCopyrightText: 2021 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ

class TezosNode < Formula
  @all_bins = []

  class << self
    attr_accessor :all_bins
  end
  homepage "https://gitlab.com/tezos/tezos"

  url "https://gitlab.com/tezos/tezos.git", :tag => "v9.0-rc1", :shallow => false

  version "v9.0-rc1-1"

  build_dependencies = %w[pkg-config autoconf rsync wget opam rustup-init]
  build_dependencies.each do |dependency|
    depends_on dependency => :build
  end

  dependencies = %w[gmp hidapi libev libffi tezos-sapling-params]
  dependencies.each do |dependency|
    depends_on dependency
  end
  desc "Entry point for initializing, configuring and running a Tezos node"

  bottle do
    root_url "https://github.com/serokell/tezos-packaging/releases/download/#{TezosNode.version}/"
    sha256 "e39f02b1cf16b5e1859e563d6949504284198d3f9a42c7b6f3e2e808f2ee8b0f" => :mojave
    sha256 "97ea6972a5a2abf55a44776e7ea0a5e1727f6df37ee8c22d51f55207cf51a239" => :catalina
    cellar :any
  end

  def make_deps
    ENV.deparallelize
    ENV["CARGO_HOME"]="./.cargo"
    system "rustup-init", "--default-toolchain", "1.44.0", "-y"
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
    install_template "src/bin_node/main.exe",
                     "_build/default/src/bin_node/main.exe",
                     "tezos-node"
  end
end
