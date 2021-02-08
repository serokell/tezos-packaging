# SPDX-FileCopyrightText: 2021 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ

require File.join(File.dirname(__FILE__), "..", "FormulaAbstract", "tezos")

class TezosBaker008Ptedotez < Tezos
  init
  desc "Daemon for baking"

  bottle do
    root_url "https://github.com/serokell/tezos-packaging/releases/download/#{TezosBaker008Ptedotez.version}/"
    cellar :any
    sha256 "401a4f9b578fc854e36f752ecfd6c9b83b167ab41201c3044495b385d17750ce" => :mojave
    sha256 "d189db274b0efd42252ddfa4888f9f25981c23427724a7bc5ac1b3366572161e" => :catalina
  end

  def install
    make_deps
    install_template "src/proto_008_PtEdoTez/bin_baker/main_baker_008_PtEdoTez.exe",
                     "_build/default/src/proto_008_PtEdoTez/bin_baker/main_baker_008_PtEdoTez.exe",
                     "tezos-baker-008-PtEdoTez"
  end
end
