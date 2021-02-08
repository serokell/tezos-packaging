# SPDX-FileCopyrightText: 2021 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ

require File.join(File.dirname(__FILE__), "..", "FormulaAbstract", "tezos")

class TezosAccuser008Ptedotez < Tezos
  init
  desc "Daemon for accusing"

  bottle do
    root_url "https://github.com/serokell/tezos-packaging/releases/download/#{TezosAccuser008Ptedotez.version}/"
    cellar :any
    sha256 "edb15ab67300edf8f79fe1d4b17f9971cf42441f0a291a99407ee7ade328e643" => :mojave
    sha256 "e83a8fb139d85c023ee63895f8650cd4c4ea3dcb705e7df6244bb6cc41a8130d" => :catalina
  end

  def install
    make_deps
    install_template "src/proto_008_PtEdoTez/bin_accuser/main_accuser_008_PtEdoTez.exe",
                     "_build/default/src/proto_008_PtEdoTez/bin_accuser/main_accuser_008_PtEdoTez.exe",
                     "tezos-accuser-008-PtEdoTez"
  end
end
