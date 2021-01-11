# SPDX-FileCopyrightText: 2021 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ

require File.join(File.dirname(__FILE__), "tezos")

class TezosBaker008Ptedotez < Tezos
  init
  desc "Daemon for baking"

  def install
    make_deps
    install_template "src/proto_008_PtEdoTez/bin_baker/main_baker_008_PtEdoTez.exe",
                     "_build/default/src/proto_008_PtEdoTez/bin_baker/main_baker_008_PtEdoTez.exe",
                     "tezos-baker-008-PtEdoTez"
  end
end
