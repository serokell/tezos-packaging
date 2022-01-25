# SPDX-FileCopyrightText: 2021 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ

class TezosSandbox < Formula
  @all_bins = []

  class << self
    attr_accessor :all_bins
  end
  homepage "https://gitlab.com/tezos/tezos"

  url "https://gitlab.com/tezos/tezos.git", :tag => "v12.0-rc2", :shallow => false

  version "v12.0-rc2-1"

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
    sha256 cellar: :any, arm64_big_sur: "0f27b3f4bd300d9627fd86096035b3822bf5f5e94fc167ea556d1631a0540d47"
  end

  def make_deps
    ENV.deparallelize
    ENV["CARGO_HOME"]="./.cargo"
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
