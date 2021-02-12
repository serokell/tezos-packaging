# SPDX-FileCopyrightText: 2021 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ

require File.join(File.dirname(__FILE__), "..", "FormulaAbstract", "tezos")

class TezosAdminClient < Tezos
  init
  desc "Administration tool for the node"

  bottle do
    root_url "https://github.com/serokell/tezos-packaging/releases/download/#{TezosAdminClient.version}/"
    cellar :any
    sha256 "c960611dff0c7a3c0be44f7f56c555a722bf4bc905cb6ba9dbd7bbcb7218d6c2" => :catalina
    sha256 "ee448cf224e05593ff8fb65188ec8df19a98e3161be96c392719779322a32c2f" => :mojave
  end

  def install
    make_deps
    install_template "src/bin_client/main_admin.exe",
                     "_build/default/src/bin_client/main_admin.exe",
                     "tezos-admin-client"
  end
end
