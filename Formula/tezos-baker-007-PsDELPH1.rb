# SPDX-FileCopyrightText: 2021 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ

require File.join(File.dirname(__FILE__), "tezos")

class TezosBaker007Psdelph1 < Tezos
  init
  desc "Daemon for baking"

  def install
    make_deps
    install_template "src/proto_007_PsDELPH1/bin_baker/main_baker_007_PsDELPH1.exe",
                     "_build/default/src/proto_007_PsDELPH1/bin_baker/main_baker_007_PsDELPH1.exe",
                     "tezos-baker-007-PsDELPH1"
  end
end
