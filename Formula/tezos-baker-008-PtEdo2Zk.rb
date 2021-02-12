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
    sha256 "b2a05a2cbed1fc6dfe9bd2025676a3a718fb976fc6d1140e7fa3b691eb72be81" => :catalina
    sha256 "68e5dc9d352e96b74e855e5cb35c7c83e37e162177d4db85a254db6409464e94" => :mojave
  end

  def install
    make_deps
    install_template "src/proto_008_PtEdo2Zk/bin_baker/main_baker_008_PtEdo2Zk.exe",
                     "_build/default/src/proto_008_PtEdo2Zk/bin_baker/main_baker_008_PtEdo2Zk.exe",
                     "tezos-baker-008-PtEdo2Zk"
  end
end
