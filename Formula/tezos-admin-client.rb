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
    sha256 "85cc3175582cf85a68fce480f5147f7717d1b3d4a7c2afe0e263be0c4055b63f" => :mojave
    sha256 "85ab3e2eefbd8de39a6daf83aa82e7b49e28b5d2908ba5dec53a30444cb597a0" => :catalina
  end

  def install
    make_deps
    install_template "src/bin_client/main_admin.exe",
                     "_build/default/src/bin_client/main_admin.exe",
                     "tezos-admin-client"
  end
end
