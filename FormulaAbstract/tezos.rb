# SPDX-FileCopyrightText: 2021 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ


# Base formula that defines parts common for all Tezos related formulas.
class Tezos < Formula
  def self.init
    @all_bins = []

    class << self
      attr_accessor :all_bins
    end
    homepage "https://gitlab.com/tezos/tezos"

    url "https://gitlab.com/tezos/tezos.git", :tag => "v8.2", :shallow => false

    version "v8.2-2"

    build_dependencies = %w[pkg-config autoconf rsync wget opam rust]
    build_dependencies.each do |dependency|
      depends_on dependency => :build
    end

    dependencies = %w[gmp hidapi libev libffi]
    dependencies.each do |dependency|
      depends_on dependency
    end
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
end
