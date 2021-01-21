# SPDX-FileCopyrightText: 2021 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ

require File.join(File.dirname(__FILE__), "tezos")

class TezosBaker007Psdelph1 < Tezos
  init
  desc "Daemon for baking"

  bottle do
    root_url "https://github.com/serokell/tezos-packaging/releases/download/v8.1-1/"
    cellar :any
    sha256 "5987ec0292c3324b2d194da55175f20490f9a2c41b23df9a9cd8355ec37dde1d" => :mojave
  end

  def install
    make_deps
    install_template "src/proto_007_PsDELPH1/bin_baker/main_baker_007_PsDELPH1.exe",
                     "_build/default/src/proto_007_PsDELPH1/bin_baker/main_baker_007_PsDELPH1.exe",
                     "tezos-baker-007-PsDELPH1"
  end
end
