# SPDX-FileCopyrightText: 2021 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ

class TezosSaplingParams < Formula
  url "https://gitlab.com/tezos/opam-repository.git", :tag => "v8.2"
  homepage "https://github.com/serokell/tezos-packaging"

  version "v8.2-3"

  desc "Sapling params required at runtime by the Tezos binaries"

  bottle do
    root_url "https://github.com/serokell/tezos-packaging/releases/download/#{TezosSaplingParams.version}/"
    cellar :any
  end

  def install
    share.mkpath
    share.install "zcash-params"
  end
end
