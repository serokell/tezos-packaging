# SPDX-FileCopyrightText: 2021 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

# TODO: once there is a new release of opam-repository this should be updated
class TezosSaplingParams < Formula
  url "https://gitlab.com/tezos/opam-repository.git", :tag => "v8.2"
  homepage "https://github.com/serokell/tezos-packaging"

  version "v8.2-3"

  desc "Sapling params required at runtime by the Tezos binaries"

  bottle do
    root_url "https://github.com/serokell/tezos-packaging/releases/download/#{TezosSaplingParams.version}/"
    sha256 cellar: :any, mojave: "4e89932b0626cffe80214ba45342280c340b34c58ebbf7c3e0185a6d4662732d"
    sha256 cellar: :any, catalina: "5f7a5687d67051eafcfb7cb5ac542143a325a135403daeca6595602bfd400441"
    sha256 cellar: :any, big_sur: "c910acffd3369bf5c4e0cff112efe6d56035394639b9571d845ad5ecb4dbd01f"
    sha256 cellar: :any, arm64_big_sur: "d7c04f2f95e459cb8639e99fb998311adc1d0babfd026987a1dcecf1e77e1f96"
  end

  def install
    share.mkpath
    share.install "zcash-params"
  end
end
