# SPDX-FileCopyrightText: 2021 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ

require File.join(File.dirname(__FILE__), "tezos")

class TezosEndorser007Psdelph1 < Tezos
  init
  desc "Daemon for endorsing"

  bottle do
    root_url "https://github.com/serokell/tezos-packaging/releases/download/#{TezosEndorser007Psdelph1.version}/"
    cellar :any
    sha256 "4c6e0eb419f2eed337d90e7177f77bb954f8a5ff6c6966605fb4f25dee759e3d" => :mojave
    sha256 "70537f634f1644d593c54598676ff921837d3f2f1f67ae5123fc09b39fbfc55b" => :catalina
  end

  def install
    make_deps
    install_template "src/proto_007_PsDELPH1/bin_endorser/main_endorser_007_PsDELPH1.exe",
                     "_build/default/src/proto_007_PsDELPH1/bin_endorser/main_endorser_007_PsDELPH1.exe",
                     "tezos-endorser-007-PsDELPH1"
  end
end
