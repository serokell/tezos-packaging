# SPDX-FileCopyrightText: 2021 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ

require File.join(File.dirname(__FILE__), "..", "FormulaAbstract", "tezos")

class TezosNode < Tezos
  init
  desc "Entry point for initializing, configuring and running a Tezos node"

  bottle do
    root_url "https://github.com/serokell/tezos-packaging/releases/download/#{TezosNode.version}/"
    cellar :any
    sha256 "8d8d844eeebb2ddc71ee49819df24d7d563d61a7a959c413ed487b2d79a51c22" => :mojave
    sha256 "cc54bc8b6232f2066c9cda469bf5815e98e9140ca311ad80d2de6efd90f3779e" => :catalina
  end

  def install
    make_deps
    install_template "src/bin_node/main.exe",
                     "_build/default/src/bin_node/main.exe",
                     "tezos-node"
  end
end
