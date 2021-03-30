# SPDX-FileCopyrightText: 2021 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ

class TezosSigner < Formula
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

  dependencies = %w[gmp hidapi libev libffi]
  dependencies.each do |dependency|
    depends_on dependency
  end
  desc "A client to remotely sign operations or blocks"

  bottle do
    root_url "https://github.com/serokell/tezos-packaging/releases/download/#{TezosSigner.version}/"
    cellar :any
    sha256 "fb36d48f47fb20d9cb4a93663c74e0eefe54e2f01f83e1c17b23ed187c733fc4" => :mojave
    sha256 "6fc1ee3ecd0b214280e0011b5e375ed4292d9ffbdca8dcf47e8b9091d71800ea" => :catalina
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
    install_template "src/bin_signer/main_signer.exe",
                     "_build/default/src/bin_signer/main_signer.exe",
                     "tezos-signer"
  end
end
