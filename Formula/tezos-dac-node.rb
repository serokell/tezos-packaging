# SPDX-FileCopyrightText: 2021 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

class TezosDacNode < Formula
  @all_bins = []

  class << self
    attr_accessor :all_bins
  end
  homepage "https://gitlab.com/tezos/tezos"

  url "https://gitlab.com/tezos/tezos.git", :tag => "v18.0", :shallow => false

  version "v18.0-1"

  build_dependencies = %w[pkg-config coreutils autoconf rsync wget rustup-init cmake]
  build_dependencies.each do |dependency|
    depends_on dependency => :build
  end

  dependencies = %w[gmp hidapi libev tezos-sapling-params]
  dependencies.each do |dependency|
    depends_on dependency
  end
  desc "A Data Availability Committee Tezos node"

  bottle do
    root_url "https://github.com/serokell/tezos-packaging/releases/download/#{TezosDacNode.version}/"
    sha256 cellar: :any, arm64_big_sur: "75165594deb395f2f0582e1659059ba37553de7f4c7f8be3f40e17d5fc8b1a4c"
    sha256 cellar: :any, big_sur: "4a9a6c3c37339d2ab1a46f90b7b9bf8cc38cc29fe35032f5e403e7567458d1ce"
    sha256 cellar: :any, monterey: "1893a3cdb2bd06240f01e5435771c8c1028b6da46a758204183fa863ee9bb8fb"
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
    # Here is the workaround to use opam 2.0.9 because Tezos is currently not compatible with opam 2.1.0 and newer
    arch = RUBY_PLATFORM.include?("arm64") ? "arm64" : "x86_64"
    system "curl", "-L", "https://github.com/ocaml/opam/releases/download/2.0.9/opam-2.0.9-#{arch}-macos", "--create-dirs", "-o", "#{ENV["HOME"]}/.opam-bin/opam"
    system "chmod", "+x", "#{ENV["HOME"]}/.opam-bin/opam"
    ENV["PATH"]="#{ENV["HOME"]}/.opam-bin:#{ENV["PATH"]}"
    system "rustup-init", "--default-toolchain", "1.64.0", "-y"
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
    install_template "src/bin_dac_node/main_dac.exe",
                     "_build/default/src/bin_dac_node/main_dac.exe",
                     "octez-dac-node"
  end
end
