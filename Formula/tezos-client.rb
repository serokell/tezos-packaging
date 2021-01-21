# SPDX-FileCopyrightText: 2021 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ

require File.join(File.dirname(__FILE__), "tezos")

class TezosClient < Tezos
  init
  desc "CLI client for interacting with tezos blockchain"

  bottle do
    root_url "https://github.com/serokell/tezos-packaging/releases/download/#{TezosClient.version}/"
    cellar :any
    sha256 "b8e78e557bda6fb821201c99d88bf04831ec49398c087dfd26586fe047bcfa11" => :mojave
    sha256 "387cfbd1a97878b40e92d0ffdc2293ef3df6945838ec8df5851fd3ea195fabfd" => :catalina
  end

  def install
    make_deps
    install_template "src/bin_client/main_client.exe",
                     "_build/default/src/bin_client/main_client.exe",
                     "tezos-client"
  end
end
