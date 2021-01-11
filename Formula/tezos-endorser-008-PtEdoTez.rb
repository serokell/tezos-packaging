# SPDX-FileCopyrightText: 2021 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ

require File.join(File.dirname(__FILE__), "tezos")

class TezosEndorser008Ptedotez < Tezos
  init
  desc "Daemon for endorsing"

  def install
    make_deps
    install_template "src/proto_008_PtEdoTez/bin_endorser/main_endorser_008_PtEdoTez.exe",
                     "_build/default/src/proto_008_PtEdoTez/bin_endorser/main_endorser_008_PtEdoTez.exe",
                     "tezos-endorser-008-PtEdoTez"
  end
end
