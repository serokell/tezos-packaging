# SPDX-FileCopyrightText: 2021 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ

require File.join(File.dirname(__FILE__), "..", "FormulaAbstract", "tezos")

class TezosBaker008Ptedo2zk < Tezos
  init
  desc "Daemon for baking"

  bottle do
    root_url "https://github.com/serokell/tezos-packaging/releases/download/#{TezosBaker008Ptedo2zk.version}/"
    cellar :any
  end

  def install
    make_deps
    install_template "src/proto_008_PtEdo2Zk/bin_baker/main_baker_008_PtEdo2Zk.exe",
                     "_build/default/src/proto_008_PtEdo2Zk/bin_baker/main_baker_008_PtEdo2Zk.exe",
                     "tezos-baker-008-PtEdo2Zk"
  end
end
