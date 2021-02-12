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
    sha256 "d6ed3d403243b29d8b55534d2258abc83a3fdecc656f87da24dd9b2c1a8b00ae" => :catalina
    sha256 "05edf9ca4dd841f1e5a364d9eb77f313bd4c55aa85bbf727e4d6202cd5b605e0" => :mojave
  end

  def install
    make_deps
    install_template "src/bin_sandbox/main.exe",
                     "_build/default/src/bin_sandbox/main.exe",
                     "tezos-sandbox"
  end
end
