# SPDX-FileCopyrightText: 2021 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ

require File.join(File.dirname(__FILE__), "tezos")

class TezosEndorser008Ptedotez < Tezos
  init
  desc "Daemon for endorsing"

  bottle do
    root_url "https://github.com/serokell/tezos-packaging/releases/download/#{TezosEndorser008Ptedotez.version}/"
    cellar :any
    sha256 "1dd1320fd2ff27a7dee5cdf9bd7c275be311ccbad9ce5b40006595ec63b1d2dd" => :mojave
    sha256 "328e3cf310114f12b60b04320c8f8f29f96e4aaee3259315008ee14d7c11d8b9" => :catalina
  end

  def install
    make_deps
    install_template "src/proto_008_PtEdoTez/bin_endorser/main_endorser_008_PtEdoTez.exe",
                     "_build/default/src/proto_008_PtEdoTez/bin_endorser/main_endorser_008_PtEdoTez.exe",
                     "tezos-endorser-008-PtEdoTez"
  end
end
