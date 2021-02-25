# SPDX-FileCopyrightText: 2021 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ

require File.join(File.dirname(__FILE__), "..", "FormulaAbstract", "tezos")

class TezosClient < Tezos
  init
  depends_on "tezos-sapling-params"
  desc "CLI client for interacting with tezos blockchain"

  bottle do
    root_url "https://github.com/serokell/tezos-packaging/releases/download/#{TezosClient.version}/"
    cellar :any
    sha256 "151a7ac18c105ec2efc4375b65b20671bfc390aca17a657538e3900944c2d238" => :mojave
    sha256 "5e7409d2ac7b7b630692c909721798242179bd0675a85693a7c50baa5453ab28" => :catalina
  end

  def install
    make_deps
    install_template "src/bin_client/main_client.exe",
                     "_build/default/src/bin_client/main_client.exe",
                     "tezos-client"
  end
end
