# SPDX-FileCopyrightText: 2019 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: MPL-2.0

# This file needs to become empty.
self: super: oself: osuper:
with oself; {
  # FIXME opam-nix needs to do this
  ocamlfind = findlib;

  # FIXME opam-nix needs to do version resolution
  ezjsonm = osuper.ezjsonm.versions."1.1.0";
  ipaddr = osuper.ipaddr.versions."4.0.0";
  conduit = osuper.conduit.versions."2.1.0";
  conduit-lwt-unix = osuper.conduit-lwt-unix.versions."2.0.2";
  cohttp-lwt-unix = osuper.cohttp-lwt-unix.versions."2.4.0";
  cohttp-lwt = osuper.cohttp-lwt.versions."2.4.0";
  macaddr = osuper.macaddr.versions."4.0.0";

  lwt = lwt4;

  # FIXME opam-nix needs to handle "external" (native) dependencies correctly
  conf-gmp = self.gmp;
  conf-libev = self.libev;
  conf-hidapi = self.hidapi;
  conf-pkg-config = self.pkg-config;

  # FIXME X11 in nixpkgs musl
  lablgtk = null;

  # FIXME recursive dependencies WTF
  bigstring = osuper.bigstring.overrideAttrs (_: { doCheck = false; });

  # FIXME vendors/index
  index = oself.index-super;

  # FIXME dependencies in tezos-protocol-compiler.opam
  tezos-protocol-compiler = osuper.tezos-protocol-compiler.overrideAttrs
    (oa: rec {
      buildInputs = oa.buildInputs ++ [ oself.pprint ];
      propagatedBuildInputs = buildInputs;
    });

  # FIXME apply this patch upstream
  tezos-stdlib-unix = osuper.tezos-stdlib-unix.overrideAttrs
    (_: { patches = [ ./stdlib-unix.patch ]; });

  tezos-client = osuper.tezos-client.overrideAttrs
    (_: { postInstall = "rm $bin/tezos-admin-client $bin/*.sh"; });

  tezos-admin-client = osuper.tezos-client.overrideAttrs (_: {
    name = "tezos-admin-client";
    postInstall = "rm $bin/tezos-client $bin/*.sh";
  });

  tezos-node =
    osuper.tezos-node.overrideAttrs (_: { postInstall = "rm $bin/*.sh"; });
}
