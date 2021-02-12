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
    sha256 "8a0dc41a239c0acd6b0cf8456b48cf2c39a40cbf1fcc93c013bf5b83198e9471" => :catalina
    sha256 "86811a82bdb4140513c831fa160a80bdcf67f12173978879d0d1d7e9632f717b" => :mojave
  end

  def install
    make_deps
    install_template "src/bin_signer/main_signer.exe",
                     "_build/default/src/bin_signer/main_signer.exe",
                     "tezos-signer"
  end
end
