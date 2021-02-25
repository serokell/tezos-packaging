# SPDX-FileCopyrightText: 2021 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ

require File.join(File.dirname(__FILE__), "..", "FormulaAbstract", "tezos")

class TezosBaker008Ptedo2zk < Tezos
  init
  depends_on "tezos-sapling-params"
  desc "Daemon for baking"

  bottle do
    root_url "https://github.com/serokell/tezos-packaging/releases/download/#{TezosBaker008Ptedo2zk.version}/"
    cellar :any
    sha256 "610e59b9bfa629fd9dbe296e22ae8009d072101dc350ce61196e0334f8068597" => :mojave
    sha256 "fa90547bfd8c21c88ba3c26cb931774a0157fcbd169e853935bc322bb5fed064" => :catalina
  end

  def install
    make_deps
    install_template "src/proto_008_PtEdo2Zk/bin_baker/main_baker_008_PtEdo2Zk.exe",
                     "_build/default/src/proto_008_PtEdo2Zk/bin_baker/main_baker_008_PtEdo2Zk.exe",
                     "tezos-baker-008-PtEdo2Zk"
  end
end
