# SPDX-FileCopyrightText: 2021 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ

class TezosAccuser008Ptedo2zk < Formula
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
  desc "Daemon for accusing"

  bottle do
    root_url "https://github.com/serokell/tezos-packaging/releases/download/#{TezosAccuser008Ptedo2zk.version}/"
    cellar :any
    sha256 "13468d11576c613a8003522cfcc4a2249fac6cffbcb7d3ad4fa75b26db0443c0" => :mojave
    sha256 "a79420d56a90c7347886b6a4fb2bbbf3c49e58c3abb067f9aaac523144eea619" => :catalina
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
    install_template "src/proto_008_PtEdo2Zk/bin_accuser/main_accuser_008_PtEdo2Zk.exe",
                     "_build/default/src/proto_008_PtEdo2Zk/bin_accuser/main_accuser_008_PtEdo2Zk.exe",
                     "tezos-accuser-008-PtEdo2Zk"
  end
end
