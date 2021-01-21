# SPDX-FileCopyrightText: 2021 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ

require File.join(File.dirname(__FILE__), "tezos")

class TezosAccuser007Psdelph1 < Tezos
  init
  desc "Daemon for accusing"

  bottle do
    root_url "https://github.com/serokell/tezos-packaging/releases/download/#{TezosAccuser007Psdelph1.version}/"
    cellar :any
    sha256 "2606f8d58c65e3331ec3a008f5f02f6f0275f11367a88abaaf7cd223d27f03a9" => :mojave
    sha256 "303f6cd063351eb94f10da9323e77d162a495ef1b92a9886eef11f3c105fb70e" => :catalina
  end

  def install
    make_deps
    install_template "src/proto_007_PsDELPH1/bin_accuser/main_accuser_007_PsDELPH1.exe",
                     "_build/default/src/proto_007_PsDELPH1/bin_accuser/main_accuser_007_PsDELPH1.exe",
                     "tezos-accuser-007-PsDELPH1"
  end
end
