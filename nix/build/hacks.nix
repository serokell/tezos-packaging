# SPDX-FileCopyrightText: 2019 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ

# This file needs to become empty.
final: prev: rec {
  tezos-protocol-compiler = prev.tezos-protocol-compiler.overrideAttrs (_: {
    postFixup = ''
      ln -s $OCAMLFIND_DESTDIR/tezos-protocol-compiler/* $OCAMLFIND_DESTDIR
    '';
  });
}
