# SPDX-FileCopyrightText: 2021 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ

require File.join(File.dirname(__FILE__), "tezos")

class TezosEndorser008Ptedotez < Tezos
  init
  desc "Daemon for endorsing"

  bottle do
    root_url "https://github.com/serokell/tezos-packaging/releases/download/v8.1-1/"
    cellar :any
    sha256 "1dd1320fd2ff27a7dee5cdf9bd7c275be311ccbad9ce5b40006595ec63b1d2dd" => :mojave
  end

  def install
    make_deps
    install_template "src/proto_008_PtEdoTez/bin_endorser/main_endorser_008_PtEdoTez.exe",
                     "_build/default/src/proto_008_PtEdoTez/bin_endorser/main_endorser_008_PtEdoTez.exe",
                     "tezos-endorser-008-PtEdoTez"
  end
end
