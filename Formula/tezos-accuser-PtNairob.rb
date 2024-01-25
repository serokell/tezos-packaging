# SPDX-FileCopyrightText: 2023 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

class TezosAccuserPtnairob < Formula
  @all_bins = []

  class << self
    attr_accessor :all_bins
  end
  homepage "https://gitlab.com/tezos/tezos"

  url "https://gitlab.com/tezos/tezos.git", :tag => "v19.0", :shallow => false

  version "v19.0-1"

  build_dependencies = %w[pkg-config coreutils autoconf rsync wget rustup-init cmake opam]
  build_dependencies.each do |dependency|
    depends_on dependency => :build
  end

  dependencies = %w[gmp hidapi libev]
  dependencies.each do |dependency|
    depends_on dependency
  end
  desc "Daemon for accusing"

  bottle do
    root_url "https://github.com/serokell/tezos-packaging/releases/download/#{TezosAccuserPtnairob.version}/"
    sha256 cellar: :any, monterey: "58695b631ff3286b6e08249166cbeabd200a995a026e76e4ad0b9a0ef2cebc12"
    sha256 cellar: :any, arm64_monterey: "2a62f3e2852db18ea72376ff69346e006f856299b232baa7bd371c5ce0148c18"
    sha256 cellar: :any, big_sur: "55724e5686be00bd3938bda2c54b3d343e97663ce566c4be599a595b9462ec1f"
    sha256 cellar: :any, arm64_big_sur: "5b450ddd46c42e39bfbb039a50e392605e1e705fdc5d143554c68d8cfe74be12"
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
    # Here is the workaround to use opam 2.0 because Tezos is currently not compatible with opam 2.1.0 and newer
    arch = RUBY_PLATFORM.include?("arm64") ? "arm64" : "x86_64"
    system "rustup-init", "--default-toolchain", "1.71.1", "-y"
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
    startup_contents =
      <<~EOS
      #!/usr/bin/env bash

      set -euo pipefail

      accuser="#{bin}/octez-accuser-PtNairob"

      accuser_config="$TEZOS_CLIENT_DIR/config"
      mkdir -p "$TEZOS_CLIENT_DIR"

      if [ ! -f "$accuser_config" ]; then
          "$accuser" --endpoint "$NODE_RPC_SCHEME://$NODE_RPC_ADDR" \
                    config init --output "$accuser_config" >/dev/null 2>&1
      else
          "$accuser" --endpoint "$NODE_RPC_SCHEME://$NODE_RPC_ADDR" \
                    config update >/dev/null 2>&1
      fi

      exec "$accuser" --endpoint "$NODE_RPC_SCHEME://$NODE_RPC_ADDR" run
    EOS
    File.write("tezos-accuser-PtNairob-start", startup_contents)
    bin.install "tezos-accuser-PtNairob-start"
    make_deps
    install_template "src/proto_017_PtNairob/bin_accuser/main_accuser_017_PtNairob.exe",
                     "_build/default/src/proto_017_PtNairob/bin_accuser/main_accuser_017_PtNairob.exe",
                     "octez-accuser-PtNairob"
  end

  service do
    run opt_bin/"tezos-accuser-PtNairob-start"
    require_root true
    environment_variables TEZOS_CLIENT_DIR: var/"lib/tezos/client", NODE_RPC_SCHEME: "http", NODE_RPC_ADDR: "localhost:8732"
    keep_alive true
    log_path var/"log/tezos-accuser-PtNairob.log"
    error_log_path var/"log/tezos-accuser-PtNairob.log"
  end

  def post_install
    mkdir "#{var}/lib/tezos/client"
  end
end
