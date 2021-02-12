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
    sha256 "f2a1dd65245399ea48f544e37467845445659522dbca01c367f6ec53a59df7c3" => :catalina
    sha256 "793fe3b61d536a0bdad18fc508a74702ab50e1c313cc740d497c6092db56e3ea" => :mojave
  end

  def install
    make_deps
    install_template "src/bin_node/main.exe",
                     "_build/default/src/bin_node/main.exe",
                     "tezos-node"
  end
end
