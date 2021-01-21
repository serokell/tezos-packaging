# SPDX-FileCopyrightText: 2021 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ

require File.join(File.dirname(__FILE__), "tezos")

class TezosEndorser007Psdelph1 < Tezos
  init
  desc "Daemon for endorsing"

  bottle do
    root_url "https://github.com/serokell/tezos-packaging/releases/download/v8.1-1/"
    cellar :any
    sha256 "4c6e0eb419f2eed337d90e7177f77bb954f8a5ff6c6966605fb4f25dee759e3d" => :mojave
  end

  def install
    make_deps
    install_template "src/proto_007_PsDELPH1/bin_endorser/main_endorser_007_PsDELPH1.exe",
                     "_build/default/src/proto_007_PsDELPH1/bin_endorser/main_endorser_007_PsDELPH1.exe",
                     "tezos-endorser-007-PsDELPH1"
  end
end
