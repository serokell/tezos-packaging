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
    sha256 "13468d11576c613a8003522cfcc4a2249fac6cffbcb7d3ad4fa75b26db0443c0" => :mojave
  end

  def install
    make_deps
    install_template "src/proto_008_PtEdo2Zk/bin_accuser/main_accuser_008_PtEdo2Zk.exe",
                     "_build/default/src/proto_008_PtEdo2Zk/bin_accuser/main_accuser_008_PtEdo2Zk.exe",
                     "tezos-accuser-008-PtEdo2Zk"
  end
end
