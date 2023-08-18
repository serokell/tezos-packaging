# SPDX-FileCopyrightText: 2021 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

class TezosAdminClient < Formula
  @all_bins = []

  class << self
    attr_accessor :all_bins
  end
  homepage "https://gitlab.com/tezos/tezos"

  url "https://gitlab.com/tezos/tezos.git", :tag => "v17.3", :shallow => false

  version "v17.3-1"

  build_dependencies = %w[pkg-config coreutils autoconf rsync wget rustup-init cmake]
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
    sha256 cellar: :any, monterey: "ea8d94c9d06ccd9832923e3915e12a1e35256e719b254de89341a1772a80b62b"
    sha256 cellar: :any, big_sur: "89b86b6f9ebdec27d9dcff19c6262a0e54f16917b244083f63581d042f1ad57f"
    sha256 cellar: :any, arm64_big_sur: "b0a7aebaaf2b6c60a6f1748ab82c2ebe456cb948deda13830f72c18917786bbb"
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
    install_template "src/bin_client/main_admin.exe",
                     "_build/default/src/bin_client/main_admin.exe",
                     "octez-admin-client"
  end
end
