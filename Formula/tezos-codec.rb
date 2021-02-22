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
    sha256 "f32315f7ce4cf3ac8f2ca34f1a211c992d89a69b8338275335921ad212d795a0" => :mojave
  end

  def install
    make_deps
    install_template "src/bin_codec/codec.exe",
                     "_build/default/src/bin_codec/codec.exe",
                     "tezos-codec"
  end
end
