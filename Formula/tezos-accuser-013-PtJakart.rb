# SPDX-FileCopyrightText: 2022 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

class TezosAccuser013Ptjakart < Formula
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
  desc "Daemon for accusing"

  bottle do
    root_url "https://github.com/serokell/tezos-packaging/releases/download/#{TezosAccuser013Ptjakart.version}/"
    sha256 cellar: :any, catalina: "84c320c327b25f3d047df4971eaf78cd64bb7685cede0aab09a37e3ea9c4a7a4"
    sha256 cellar: :any, catalina: "84c320c327b25f3d047df4971eaf78cd64bb7685cede0aab09a37e3ea9c4a7a4"
    sha256 cellar: :any, catalina: "84c320c327b25f3d047df4971eaf78cd64bb7685cede0aab09a37e3ea9c4a7a4"
    sha256 cellar: :any, big_sur: "e6418258cfe5942abf18f1b139d28271e824a6aa49e3e889de98381512bee7df"
    sha256 cellar: :any, arm64_big_sur: "08a3ac1dfa299aa34eedbf0deff66558e12fc850c51a1abf0e414d94f2423cd4"
    sha256 cellar: :any, catalina: "84c320c327b25f3d047df4971eaf78cd64bb7685cede0aab09a37e3ea9c4a7a4"
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
    startup_contents =
      <<~EOS
      #!/usr/bin/env bash

      set -euo pipefail

      accuser="#{bin}/tezos-accuser-013-PtJakart"

      accuser_dir="$DATA_DIR"

      accuser_config="$accuser_dir/config"
      mkdir -p "$accuser_dir"

      if [ ! -f "$accuser_config" ]; then
          "$accuser" --base-dir "$accuser_dir" \
                    --endpoint "$NODE_RPC_ENDPOINT" \
                    config init --output "$accuser_config" >/dev/null 2>&1
      else
          "$accuser" --base-dir "$accuser_dir" \
                    --endpoint "$NODE_RPC_ENDPOINT" \
                    config update >/dev/null 2>&1
      fi

      exec "$accuser" --base-dir "$accuser_dir" \
          --endpoint "$NODE_RPC_ENDPOINT" \
          run
    EOS
    File.write("tezos-accuser-013-PtJakart-start", startup_contents)
    bin.install "tezos-accuser-013-PtJakart-start"
    make_deps
    install_template "src/proto_013_PtJakart/bin_accuser/main_accuser_013_PtJakart.exe",
                     "_build/default/src/proto_013_PtJakart/bin_accuser/main_accuser_013_PtJakart.exe",
                     "tezos-accuser-013-PtJakart"
  end

  plist_options manual: "tezos-accuser-013-PtJakart run"
  def plist
    <<~EOS
      <?xml version="1.0" encoding="UTF-8"?>
      <!DOCTYPE plist PUBLIC "-//Apple Computer//DTD PLIST 1.0//EN"
      "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
      <plist version="1.0">
        <dict>
          <key>Label</key>
          <string>#{plist_name}</string>
          <key>Program</key>
          <string>#{opt_bin}/tezos-accuser-013-PtJakart-start</string>
          <key>EnvironmentVariables</key>
            <dict>
              <key>DATA_DIR</key>
              <string>#{var}/lib/tezos/client</string>
              <key>NODE_RPC_ENDPOINT</key>
              <string>http://localhost:8732</string>
          </dict>
          <key>RunAtLoad</key><true/>
          <key>StandardOutPath</key>
          <string>#{var}/log/#{name}.log</string>
          <key>StandardErrorPath</key>
          <string>#{var}/log/#{name}.log</string>
        </dict>
      </plist>
    EOS
  end
  def post_install
    mkdir "#{var}/lib/tezos/client"
  end
end
