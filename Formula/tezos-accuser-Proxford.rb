# SPDX-FileCopyrightText: 2023 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

class TezosAccuserProxford < Formula
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

  dependencies = %w[gmp hidapi libev]
  dependencies.each do |dependency|
    depends_on dependency
  end
  desc "Daemon for accusing"

  bottle do
    root_url "https://github.com/serokell/tezos-packaging/releases/download/#{TezosAccuserProxford.version}/"
    sha256 cellar: :any, monterey: "6f7d9fd9bbb469d0b1ad03bacfc0f98f68b74a144cc6829fadf5743cd5d2e5b2"
  end

  def make_deps
    ENV.deparallelize
    ENV["CARGO_HOME"]="./.cargo"
    # Disable usage of instructions from the ADX extension to avoid incompatibility
    # with old CPUs, see https://gitlab.com/dannywillems/ocaml-bls12-381/-/merge_requests/135/
    ENV["BLST_PORTABLE"]="yes"
    # Here is the workaround to use opam 2.0 because Tezos is currently not compatible with opam 2.1.0 and newer
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
    startup_contents =
      <<~EOS
      #!/usr/bin/env bash

      set -euo pipefail

      accuser="#{bin}/octez-accuser-Proxford"

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
    File.write("tezos-accuser-Proxford-start", startup_contents)
    bin.install "tezos-accuser-Proxford-start"
    make_deps
    install_template "src/proto_018_Proxford/bin_accuser/main_accuser_018_Proxford.exe",
                     "_build/default/src/proto_018_Proxford/bin_accuser/main_accuser_018_Proxford.exe",
                     "octez-accuser-Proxford"
  end

  service do
    run opt_bin/"tezos-accuser-Proxford-start"
    require_root true
    environment_variables TEZOS_CLIENT_DIR: var/"lib/tezos/client", NODE_RPC_SCHEME: "http", NODE_RPC_ADDR: "localhost:8732"
    keep_alive true
    log_path var/"log/tezos-accuser-Proxford.log"
    error_log_path var/"log/tezos-accuser-Proxford.log"
  end

  def post_install
    mkdir "#{var}/lib/tezos/client"
  end
end
