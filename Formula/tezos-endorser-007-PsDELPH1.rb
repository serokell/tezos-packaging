# SPDX-FileCopyrightText: 2021 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ

require File.join(File.dirname(__FILE__), "..", "FormulaAbstract", "tezos")

class TezosEndorser007Psdelph1 < Tezos
  init
  desc "Daemon for endorsing"

  bottle do
    root_url "https://github.com/serokell/tezos-packaging/releases/download/#{TezosEndorser007Psdelph1.version}/"
    cellar :any
    sha256 "474040ee021cd5df167ef2aa8078f8169d26f6574475170de0f067015aff46a8" => :catalina
  end

  def install
    make_deps
    install_template "src/proto_007_PsDELPH1/bin_endorser/main_endorser_007_PsDELPH1.exe",
                     "_build/default/src/proto_007_PsDELPH1/bin_endorser/main_endorser_007_PsDELPH1.exe",
                     "tezos-endorser-007-PsDELPH1"
  end
end
