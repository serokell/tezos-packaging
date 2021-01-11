# SPDX-FileCopyrightText: 2021 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ

require File.join(File.dirname(__FILE__), "tezos")

class TezosAccuser008Ptedotez < Tezos
  init
  desc "Daemon for accusing"

  def install
    make_deps
    install_template "src/proto_008_PtEdoTez/bin_accuser/main_accuser_008_PtEdoTez.exe",
                     "_build/default/src/proto_008_PtEdoTez/bin_accuser/main_accuser_008_PtEdoTez.exe",
                     "tezos-accuser-008-PtEdoTez"
  end
end
