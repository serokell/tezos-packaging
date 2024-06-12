#! /usr/bin/env bash
# SPDX-FileCopyrightText: 2021 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

# This script tests ../../scripts/bottle-hashes.sh by generating
# a dummy brew bottle, running bottle-hashes.sh on it, and checking
# that the test brew formula now has the expected information.

bottle_dir="./bottles"

mkdir -p $bottle_dir
mkdir -p ./Formula

# Generate a dummy formula
formula_name="tezos-hash-test"

cat >./Formula/$formula_name.rb <<EOL
class TezosHashTest < Formula
  homepage "https://github.com/serokell/tezos-packaging"

  url "https://github.com/serokell/tezos-packaging", :tag => "v0.0", :shallow => false

  version "v0.0-1"

  desc "Dummy formula to test automated bottle hash insertion"

  bottle do
    root_url "https://github.com/serokell/tezos-packaging/releases/download/#{TezosHashTest.version}/"
  end

  def install
  end
end
EOL

monterey_bottle="$formula_name-v0.0-0.monterey.bottle.tar.gz"

# Generate some dummy bottles
dd if=/dev/urandom of=$bottle_dir/$monterey_bottle count=2000 status=none

# Run the hash inserting script
../../scripts/bottle-hashes.sh "$bottle_dir" "v0.0-1"

# Assert the info was inserted correctly
monterey_hash="$(sha256sum $bottle_dir/$monterey_bottle | cut -d " " -f 1)"

expected_formula=$(cat << EOF
class TezosHashTest < Formula
  homepage "https://github.com/serokell/tezos-packaging"

  url "https://github.com/serokell/tezos-packaging", :tag => "v0.0", :shallow => false

  version "v0.0-1"

  desc "Dummy formula to test automated bottle hash insertion"

  bottle do
    root_url "https://github.com/serokell/tezos-packaging/releases/download/#{TezosHashTest.version}/"
    sha256 cellar: :any, monterey: "$monterey_hash"
  end

  def install
  end
end
EOF
)

if [[ $(< ./Formula/$formula_name.rb) != "$expected_formula" ]]; then
    echo "bottle-hashes.sh did not produce the expected output. Expected:"
    echo "$expected_formula"
    echo -e "\nGot:"
    cat ./Formula/$formula_name.rb
    exit 1
fi

rm -r ./Formula
rm -r ./bottles
