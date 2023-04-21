# SPDX-FileCopyrightText: 2021-2022 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

# This file needs to become empty.
self: super: rec {
  octez-protocol-compiler = super.octez-protocol-compiler.overrideAttrs (_: {
    postFixup = ''
      ln -s $OCAMLFIND_DESTDIR/octez-protocol-compiler/* $OCAMLFIND_DESTDIR
    '';
  });
  # For some reason octez-protocol-compiler wants some docs to be present in tezos-protocol-environment
  tezos-protocol-environment = super.tezos-protocol-environment.overrideAttrs (o: {
    postFixup = ''
      DUMMY_DOCS_DIR="$OCAMLFIND_DESTDIR/../doc/${o.pname}"
      mkdir -p "$DUMMY_DOCS_DIR"
      for doc in "README.md" "CHANGES.rst" "LICENSE"; do
        touch "$DUMMY_DOCS_DIR/$doc"
      done
    '';
  });
  octez-admin-client = super.octez-client.overrideAttrs (_ : {
    name = "octez-admin-client";
    postInstall = "rm $out/bin/octez-client $out/bin/*.sh";
  });
  octez-client = super.octez-client.overrideAttrs (_ : {
    postInstall = "rm $out/bin/octez-admin-client $out/bin/*.sh";
  });
  octez-node = super.octez-node.overrideAttrs (_ : {
    postInstall = "rm $out/bin/*.sh";
  });
  ocamlfind = super.ocamlfind.overrideAttrs (drv: {
    patches = [ ./install_topfind_196.patch ];
  });
}
