# SPDX-FileCopyrightText: 2021 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

class TezosAdminClient < Formula
  @all_bins = []

  class << self
    attr_accessor :all_bins
  end
  homepage "https://gitlab.com/tezos/tezos"

  url "https://gitlab.com/tezos/tezos.git", :tag => "v13.0", :shallow => false

  version "v13.0-1"

  build_dependencies = %w[pkg-config autoconf rsync wget rustup-init]
  build_dependencies.each do |dependency|
    depends_on dependency => :build
  end

  dependencies = %w[gmp hidapi libev libffi]
  dependencies.each do |dependency|
    depends_on dependency
  end
  desc "Administration tool for the node"

  bottle do
    root_url "https://github.com/serokell/tezos-packaging/releases/download/#{TezosAdminClient.version}/"
    sha256 cellar: :any, catalina: "739c675926396d9a11fcf62e33ba07fc80774f6dc0a74e3ce08d99cc1f9dd9d7"
    sha256 cellar: :any, big_sur: "66440791b22d8b78bfde2d12b6f94406812422aa1da7a7eadaaffba857d6d731"
    sha256 cellar: :any, arm64_big_sur: "1728ca20ae075237b091c41b31167b64a5d88e769e2bf5c14d3b6f569e79cb89"
    sha256 cellar: :any, catalina: "739c675926396d9a11fcf62e33ba07fc80774f6dc0a74e3ce08d99cc1f9dd9d7"
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
    install_template "src/bin_client/main_admin.exe",
                     "_build/default/src/bin_client/main_admin.exe",
                     "tezos-admin-client"
  end
end
