# SPDX-FileCopyrightText: 2021 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ

require File.join(File.dirname(__FILE__), "..", "FormulaAbstract", "tezos")

class TezosSigner < Tezos
  init
  desc "A client to remotely sign operations or blocks"

  bottle do
    root_url "https://github.com/serokell/tezos-packaging/releases/download/#{TezosSigner.version}/"
    cellar :any
    sha256 "13df7e1edca72b3425ea8afb6d5230908e91d7a51d64be55f0c128a51a53c614" => :mojave
    sha256 "58b7ec819ce51e2ac1af4c7794c7030d5f4b6e7d647216b40e69c6bcc2d155f4" => :catalina
  end

  def install
    make_deps
    install_template "src/bin_signer/main_signer.exe",
                     "_build/default/src/bin_signer/main_signer.exe",
                     "tezos-signer"
  end
end
