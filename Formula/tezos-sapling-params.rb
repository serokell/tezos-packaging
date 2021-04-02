# SPDX-FileCopyrightText: 2021 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ

# TODO: once there is a new release of opam-repository this should be updated
class TezosSaplingParams < Formula
  url "https://gitlab.com/tezos/opam-repository.git", :tag => "v8.2"
  homepage "https://github.com/serokell/tezos-packaging"

  version "v8.2-3"

  desc "Sapling params required at runtime by the Tezos binaries"

  bottle do
    root_url "https://github.com/serokell/tezos-packaging/releases/download/#{TezosSaplingParams.version}/"
    sha256 "93d730b5569ea10d66ce85423acc975355ac23fe698fda0445f3799fb20a1e01" => :mojave
    sha256 "2921c9a5bec843fbd3806660ae4911d43ff2fac7adc2ccaee674e7bfc27d3771" => :catalina
    cellar :any
  end

  def install
    share.mkpath
    share.install "zcash-params"
  end
end