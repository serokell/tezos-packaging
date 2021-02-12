# SPDX-FileCopyrightText: 2021 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ

require File.join(File.dirname(__FILE__), "..", "FormulaAbstract", "tezos")

class TezosCodec < Tezos
  init
  desc "A client to decode and encode JSON"

  bottle do
    root_url "https://github.com/serokell/tezos-packaging/releases/download/#{TezosCodec.version}/"
    cellar :any
    sha256 "aeab96953b1014aa5009cc89e4919b111a24d33192c452849387721bd030be94" => :catalina
    sha256 "b623e5bdbdada505839e00dcd39aab7fefc64891a96145748b58bbd21a9621c2" => :mojave
  end

  def install
    make_deps
    install_template "src/bin_codec/codec.exe",
                     "_build/default/src/bin_codec/codec.exe",
                     "tezos-codec"
  end
end
