# SPDX-FileCopyrightText: 2021 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ

class TezosEndorser010Ptgranad < Formula
  @all_bins = []

  class << self
    attr_accessor :all_bins
  end
  homepage "https://gitlab.com/tezos/tezos"

  url "https://gitlab.com/tezos/tezos.git", :tag => "v10.3", :shallow => false

  version "v10.3-1"

  build_dependencies = %w[pkg-config autoconf rsync wget rustup-init]
  build_dependencies.each do |dependency|
    depends_on dependency => :build
  end

  dependencies = %w[gmp hidapi libev libffi]
  dependencies.each do |dependency|
    depends_on dependency
  end

  desc "Daemon for endorsing"

  bottle do
    root_url "https://github.com/serokell/tezos-packaging/releases/download/#{TezosEndorser010Ptgranad.version}/"
    sha256 cellar: :any, catalina: "f323de354dd65525784662a6401cbb899dbb9c495807cdb89664e4fdd63ed550"
    sha256 cellar: :any, mojave: "a8d2131a794a2f9bf5bd88b2c916593b4a8bd29cc7da75f6991cd22b033552dc"
  end

  def make_deps
    ENV.deparallelize
    ENV["CARGO_HOME"]="./.cargo"
    # Here is the workaround to use opam 2.0.9 because Tezos is currently not compatible with opam 2.1.0 and newer
    system "curl", "-L", "https://github.com/ocaml/opam/releases/download/2.0.9/opam-2.0.9-x86_64-macos", "--create-dirs", "-o", "#{ENV["HOME"]}/.opam-bin/opam"
    system "chmod", "+x", "#{ENV["HOME"]}/.opam-bin/opam"
    ENV["PATH"]="#{ENV["HOME"]}/.opam-bin:#{ENV["PATH"]}"
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
    startup_contents =
      <<~EOS
      #!/usr/bin/env bash

      set -euo pipefail

      endorser="#{bin}/tezos-endorser-010-PtGRANAD"

      endorser_dir="$DATA_DIR"

      endorser_config="$endorser_dir/config"
      mkdir -p "$endorser_dir"

      if [ ! -f "$endorser_config" ]; then
          "$endorser" --base-dir "$endorser_dir" \
                      --endpoint "$NODE_RPC_ENDPOINT" \
                      config init --output "$endorser_config" >/dev/null 2>&1
      else
          "$endorser" --base-dir "$endorser_dir" \
                      --endpoint "$NODE_RPC_ENDPOINT" \
                      config update >/dev/null 2>&1
      fi

      launch_endorser() {
          exec "$endorser" --base-dir "$endorser_dir" \
              --endpoint "$NODE_RPC_ENDPOINT" \
              run "$@"
      }

      if [[ -z "$ENDORSER_ACCOUNT" ]]; then
          launch_endorser
      else
          launch_endorser "$ENDORSER_ACCOUNT"
      fi
    EOS
    File.write("tezos-endorser-010-PtGRANAD-start", startup_contents)
    bin.install "tezos-endorser-010-PtGRANAD-start"
    make_deps
    install_template "src/proto_010_PtGRANAD/bin_endorser/main_endorser_010_PtGRANAD.exe",
                     "_build/default/src/proto_010_PtGRANAD/bin_endorser/main_endorser_010_PtGRANAD.exe",
                     "tezos-endorser-010-PtGRANAD"
  end

  plist_options manual: "tezos-endorser-010-PtGRANAD run"
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
          <string>#{opt_bin}/tezos-endorser-010-PtGRANAD-start</string>
          <key>EnvironmentVariables</key>
            <dict>
              <key>DATA_DIR</key>
              <string>#{var}/lib/tezos/client</string>
              <key>NODE_RPC_ENDPOINT</key>
              <string>http://localhost:8732</string>
              <key>ENDORSER_ACCOUNT</key>
              <string></string>
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
