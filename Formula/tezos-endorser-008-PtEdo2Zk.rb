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
    sha256 "a8e4e417b2e7a4a75285f68bd1fe4d6616a93c236e1c93ac1776be93c3de361d" => :mojave
    sha256 "7397cb5980f0c1467fa095eeb0d8d99cbbb5cdf0b843e1f84ffc70d6eb03a902" => :catalina
  end

  def install
    make_deps
    install_template "src/proto_008_PtEdo2Zk/bin_endorser/main_endorser_008_PtEdo2Zk.exe",
                     "_build/default/src/proto_008_PtEdo2Zk/bin_endorser/main_endorser_008_PtEdo2Zk.exe",
                     "tezos-endorser-008-PtEdo2Zk"
  end
end
