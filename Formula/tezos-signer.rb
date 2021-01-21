# SPDX-FileCopyrightText: 2021 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ

require File.join(File.dirname(__FILE__), "tezos")

class TezosSigner < Tezos
  init
  desc "A client to remotely sign operations or blocks"

  bottle do
    root_url "https://github.com/serokell/tezos-packaging/releases/download/v8.1-1/"
    cellar :any
    sha256 "b9ff4fd61589fdd085ac39fac79ed4bf4e7557ca25a69a7dcab3060fc951a62f" => :mojave
  end

  def install
    make_deps
    install_template "src/bin_signer/main_signer.exe",
                     "_build/default/src/bin_signer/main_signer.exe",
                     "tezos-signer"
  end
end
