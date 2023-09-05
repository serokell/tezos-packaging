# SPDX-FileCopyrightText: 2021-2022 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

# This file needs to become empty.
self: super: rec {
  # For some reason octez-protocol-compiler wants some docs to be present in octez-libs
  octez-libs = super.octez-libs.overrideAttrs (o: {
    postFixup = ''
      DUMMY_DOCS_DIR="$OCAMLFIND_DESTDIR/../doc/${o.pname}"
      mkdir -p "$DUMMY_DOCS_DIR"
      for doc in "README.md" "CHANGES.rst" "LICENSE"; do
        touch "$DUMMY_DOCS_DIR/$doc"
      done

      DUMMY_ODOC_PAGES_DIR="$DUMMY_DOCS_DIR/odoc-pages"
      mkdir -p "$DUMMY_ODOC_PAGES_DIR"
      for doc in "tezos_workers.mld" "tezos_lwt_result_stdlib.mld" "index.mld"; do
        touch "$DUMMY_ODOC_PAGES_DIR/$doc"
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
