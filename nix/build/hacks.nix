# SPDX-FileCopyrightText: 2021-2022 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

# This file needs to become empty.
self: super: rec {
  tezos-protocol-compiler = super.tezos-protocol-compiler.overrideAttrs (_: {
    postFixup = ''
      ln -s $OCAMLFIND_DESTDIR/tezos-protocol-compiler/* $OCAMLFIND_DESTDIR
    '';
  });
  tezos-admin-client = super.tezos-client.overrideAttrs (_ : {
    name = "tezos-admin-client";
    postInstall = "rm $out/bin/tezos-client $out/bin/*.sh";
  });
  tezos-client = super.tezos-client.overrideAttrs (_ : {
    postInstall = "rm $out/bin/tezos-admin-client $out/bin/*.sh";
  });
  tezos-node = super.tezos-node.overrideAttrs (_ : {
    postInstall = "rm $out/bin/*.sh";
  });
}
