# SPDX-FileCopyrightText: 2021 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ

require File.join(File.dirname(__FILE__), "tezos")

class TezosCodec < Tezos
  init
  desc "A client to decode and encode JSON"

  bottle do
    root_url "https://github.com/serokell/tezos-packaging/releases/download/#{TezosCodec.version}/"
    cellar :any
    sha256 "3be0ac706f19bd6a673dd64c5d20b7973b353d80273dc56f3905cb39e6acc03d" => :mojave
    sha256 "e738541a16f804f74c4e35ef1a03f6af6fa7a2d42c2adcd7191cde63bc8b1d17" => :catalina
  end

  def install
    make_deps
    install_template "src/bin_codec/codec.exe",
                     "_build/default/src/bin_codec/codec.exe",
                     "tezos-codec"
  end
end
