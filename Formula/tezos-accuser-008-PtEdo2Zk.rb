# SPDX-FileCopyrightText: 2021 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ

require File.join(File.dirname(__FILE__), "..", "FormulaAbstract", "tezos")

class TezosAccuser008Ptedo2zk < Tezos
  init
  desc "Daemon for accusing"

  bottle do
    root_url "https://github.com/serokell/tezos-packaging/releases/download/#{TezosAccuser008Ptedo2zk.version}/"
    cellar :any
    sha256 "c5e5e21e6413c8a669ae1febedbaf294814cb98bb27f43b16d8e02ff11b82f21" => :catalina
    sha256 "3c949e4a73f233f067dce4c5c99ea0b7717b4009eaed2a39b0db0f576c4c3982" => :mojave
  end

  def install
    make_deps
    install_template "src/proto_008_PtEdo2Zk/bin_accuser/main_accuser_008_PtEdo2Zk.exe",
                     "_build/default/src/proto_008_PtEdo2Zk/bin_accuser/main_accuser_008_PtEdo2Zk.exe",
                     "tezos-accuser-008-PtEdo2Zk"
  end
end
