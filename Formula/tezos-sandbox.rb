# SPDX-FileCopyrightText: 2021 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ

require File.join(File.dirname(__FILE__), "..", "FormulaAbstract", "tezos")

class TezosSandbox < Tezos
  init
  desc "A tool for setting up and running testing scenarios with the local blockchain"

  bottle do
    root_url "https://github.com/serokell/tezos-packaging/releases/download/#{TezosSandbox.version}/"
    cellar :any
    sha256 "7fc301036da8c383feedae58d65fe5eabac199d5c58de9b024f5c58a62797301" => :mojave
    sha256 "b95c1223b2fa917ff7bbe1bcd4312033035977d1cf87857b5b62e360779f9e43" => :catalina
  end

  def install
    make_deps
    install_template "src/bin_sandbox/main.exe",
                     "_build/default/src/bin_sandbox/main.exe",
                     "tezos-sandbox"
  end
end
