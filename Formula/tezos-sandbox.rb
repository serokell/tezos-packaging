# SPDX-FileCopyrightText: 2021 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

class TezosSandbox < Formula
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

  dependencies = %w[gmp hidapi libev libffi coreutils util-linux]
  dependencies.each do |dependency|
    depends_on dependency
  end
  desc "A tool for setting up and running testing scenarios with the local blockchain"

  bottle do
    root_url "https://github.com/serokell/tezos-packaging/releases/download/#{TezosSandbox.version}/"
    sha256 cellar: :any, catalina: "558e7df1c0e8072a136518321dcd2f05fef33ee464903ff1f03fff9f7f3c5651"
    sha256 cellar: :any, big_sur: "1b60bc69094a2a2caeba7bd44ae48acf41830cda53c57ff3879c89907448943c"
    sha256 cellar: :any, arm64_big_sur: "62b7ba85aea0bbe693d05910b22c662aa9afedfd82e69037284be3e413daa892"
    sha256 cellar: :any, catalina: "558e7df1c0e8072a136518321dcd2f05fef33ee464903ff1f03fff9f7f3c5651"
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
    install_template "src/bin_sandbox/main.exe",
                     "_build/default/src/bin_sandbox/main.exe",
                     "tezos-sandbox"
  end

  # homebrew does not allow for post-setup modification of user files,
  # so we have to provide a caveat to be displayed for the user to adjust $PATH manually
  def caveats
    <<~EOS
      tezos-sandbox depends on 'coreutils' and 'util-linux', which have been installed. Please run the following command to bring them in scope:
        export PATH=#{HOMEBREW_PREFIX}/opt/coreutils/libexec/gnubin:#{HOMEBREW_PREFIX}/opt/util-linux/bin:$PATH
    EOS
  end
end
