# SPDX-FileCopyrightText: 2021 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ

class TezosSandbox < Formula
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
  desc "A tool for setting up and running testing scenarios with the local blockchain"

  bottle do
    root_url "https://github.com/serokell/tezos-packaging/releases/download/#{TezosSandbox.version}/"
    cellar :any
    sha256 "7fc301036da8c383feedae58d65fe5eabac199d5c58de9b024f5c58a62797301" => :mojave
    sha256 "b95c1223b2fa917ff7bbe1bcd4312033035977d1cf87857b5b62e360779f9e43" => :catalina
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
    install_template "src/bin_sandbox/main.exe",
                     "_build/default/src/bin_sandbox/main.exe",
                     "tezos-sandbox"
  end
end
