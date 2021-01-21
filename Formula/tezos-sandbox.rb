# SPDX-FileCopyrightText: 2021 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ

require File.join(File.dirname(__FILE__), "tezos")

class TezosSandbox < Tezos
  init
  desc "A tool for setting up and running testing scenarios with the local blockchain"

  bottle do
    root_url "https://github.com/serokell/tezos-packaging/releases/download/v8.1-1/"
    cellar :any
    sha256 "1a72776411771d6970aa1b2ea9c4dee5680f2b097b3824bb91b9c93a951d5cf2" => :mojave
  end

  def install
    make_deps
    install_template "src/bin_sandbox/main.exe",
                     "_build/default/src/bin_sandbox/main.exe",
                     "tezos-sandbox"
  end
end
