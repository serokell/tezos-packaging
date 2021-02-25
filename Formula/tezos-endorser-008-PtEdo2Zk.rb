# SPDX-FileCopyrightText: 2021 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ

class TezosEndorser008Ptedo2zk < Formula
  @all_bins = []

  class << self
    attr_accessor :all_bins
  end
  homepage "https://gitlab.com/tezos/tezos"

  url "https://gitlab.com/tezos/tezos.git", :tag => "v8.2", :shallow => false

  version "v8.2-3"

  build_dependencies = %w[pkg-config autoconf rsync wget opam rust]
  build_dependencies.each do |dependency|
    depends_on dependency => :build
  end

  dependencies = %w[gmp hidapi libev libffi]
  dependencies.each do |dependency|
    depends_on dependency
  end

  desc "Daemon for endorsing"

  bottle do
    root_url "https://github.com/serokell/tezos-packaging/releases/download/#{TezosEndorser008Ptedo2zk.version}/"
    cellar :any
    sha256 "a8e4e417b2e7a4a75285f68bd1fe4d6616a93c236e1c93ac1776be93c3de361d" => :mojave
    sha256 "7397cb5980f0c1467fa095eeb0d8d99cbbb5cdf0b843e1f84ffc70d6eb03a902" => :catalina
  end

  def make_deps
    ENV.deparallelize

    system "opam", "init", "--bare", "--debug", "--auto-setup", "--disable-sandboxing"

    ENV["RUST_VERSION"] = "1.49.0"
    system "make", "build-deps"
  end

  def install_template(dune_path, exec_path, name)
    bin.mkpath
    self.class.all_bins << name
    system ["eval $(opam env)", "dune build #{dune_path}", "cp #{exec_path} #{name}"].join(" && ")
    bin.install name
  end


  def install
    make_deps
    install_template "src/proto_008_PtEdo2Zk/bin_endorser/main_endorser_008_PtEdo2Zk.exe",
                     "_build/default/src/proto_008_PtEdo2Zk/bin_endorser/main_endorser_008_PtEdo2Zk.exe",
                     "tezos-endorser-008-PtEdo2Zk"
  end
end
