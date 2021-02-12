# SPDX-FileCopyrightText: 2021 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ

require File.join(File.dirname(__FILE__), "..", "FormulaAbstract", "tezos")

class TezosAccuser007Psdelph1 < Tezos
  init
  desc "Daemon for accusing"

  bottle do
    root_url "https://github.com/serokell/tezos-packaging/releases/download/#{TezosAccuser007Psdelph1.version}/"
    cellar :any
    sha256 "de6b8c02b8dffd110acd290a451e2a351e9f37b173eac22f4963a0b7bc3913ea" => :catalina
    sha256 "fd1c2993b4836bed3b26006dd86db50b603ccd1c9f38cbb486a52d3c473a35dd" => :mojave
  end

  def install
    make_deps
    install_template "src/proto_007_PsDELPH1/bin_accuser/main_accuser_007_PsDELPH1.exe",
                     "_build/default/src/proto_007_PsDELPH1/bin_accuser/main_accuser_007_PsDELPH1.exe",
                     "tezos-accuser-007-PsDELPH1"
  end
end
