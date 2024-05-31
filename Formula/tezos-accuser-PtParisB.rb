# SPDX-FileCopyrightText: 2024 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

class TezosAccuserPtparisb < Formula
  @all_bins = []

  class << self
    attr_accessor :all_bins
  end
  homepage "https://gitlab.com/tezos/tezos"

  url "https://gitlab.com/tezos/tezos.git", :tag => "octez-v20.0", :shallow => false

  version "v20.0-1"

  build_dependencies = %w[pkg-config coreutils autoconf rsync wget rustup-init cmake opam]
  build_dependencies.each do |dependency|
    depends_on dependency => :build
  end

  dependencies = %w[gmp hidapi libev protobuf sqlite]
  dependencies.each do |dependency|
    depends_on dependency
  end
  desc "Daemon for accusing"

  bottle do
    root_url "https://github.com/serokell/tezos-packaging/releases/download/#{TezosAccuserPtparisb.version}/"
    sha256 cellar: :any, monterey: "10685121a02dd9002d16a119c29bccad4fc59b8d7f6c8e250b935d8457d30b6e"
    sha256 cellar: :any, arm64_monterey: "bb3d2c6b727d077ed62e039f7e2093a139e57e559b72421d727dd408a9032eff"
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

      accuser="#{bin}/octez-accuser-PtParisB"

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
    File.write("tezos-accuser-PtParisB-start", startup_contents)
    bin.install "tezos-accuser-PtParisB-start"
    make_deps
    install_template "src/proto_019_PtParisB/bin_accuser/main_accuser_019_PtParisB.exe",
                     "_build/default/src/proto_019_PtParisB/bin_accuser/main_accuser_019_PtParisB.exe",
                     "octez-accuser-PtParisB"
  end

  service do
    run opt_bin/"tezos-accuser-PtParisB-start"
    require_root true
    environment_variables TEZOS_CLIENT_DIR: var/"lib/tezos/client", NODE_RPC_SCHEME: "http", NODE_RPC_ADDR: "localhost:8732"
    keep_alive true
    log_path var/"log/tezos-accuser-PtParisB.log"
    error_log_path var/"log/tezos-accuser-PtParisB.log"
  end

  def post_install
    mkdir "#{var}/lib/tezos/client"
  end
end
