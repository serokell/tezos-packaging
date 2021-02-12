# SPDX-FileCopyrightText: 2021 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ

require File.join(File.dirname(__FILE__), "..", "FormulaAbstract", "tezos")

class TezosEndorser008Ptedo2zk < Tezos
  init
  desc "Daemon for endorsing"

  bottle do
    root_url "https://github.com/serokell/tezos-packaging/releases/download/#{TezosEndorser008Ptedo2zk.version}/"
    cellar :any
    sha256 "24ed930b86471a647840b15405d91fa2a7f0215b12196e36a266442e6e5492b1" => :catalina
  end

  def install
    make_deps
    install_template "src/proto_008_PtEdo2Zk/bin_endorser/main_endorser_008_PtEdo2Zk.exe",
                     "_build/default/src/proto_008_PtEdo2Zk/bin_endorser/main_endorser_008_PtEdo2Zk.exe",
                     "tezos-endorser-008-PtEdo2Zk"
  end
end
