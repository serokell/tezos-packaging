# SPDX-FileCopyrightText: 2019 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ

# This file needs to become empty.
self: super: oself: osuper:
with oself; rec {
  ocaml = self.ocaml-ng.ocamlPackages_4_09.ocaml.overrideAttrs (o: o // {
    hardeningDisable = o.hardeningDisable ++
                       self.stdenv.lib.optional self.stdenv.hostPlatform.isMusl "pie";
  });
  # FIXME opam-nix needs to do this
  ocamlfind = findlib;

  ocamlgraph = osuper.ocamlgraph.override (_: { gtkSupport = false; });

  # FIXME opam-nix needs to do version resolution
  ezjsonm = osuper.ezjsonm.versions."1.1.0";
  ipaddr = osuper.ipaddr.versions."4.0.0".overrideAttrs (_: {
    minimumOCamlVersion = "4.07";
  });

  # Here we pin old tls version because more recent versions
  # cannot be build with dune < 2.0.0, which will require
  # to override dune version for huge amount of dependencies.
  # Also opam-nix currently unable to build tls package, so
  # we build it in a bit hacky way.
  tls = osuper.tls.versions."0.10.6".overrideAttrs (o: {
    outputs = [ "out" ];
    buildInputs = o.buildInputs ++ [ topkg ];
    buildPhase = ''
      ${topkg.run} build --tests false --with-mirage false --with-lwt true
    '';
    checkPhase = "${topkg.run} test";
    inherit (topkg) installPhase;
  });
  x509 = osuper.x509.versions."0.9.0";
  conduit = osuper.conduit.versions."2.1.0".overrideAttrs (oa: rec {
    buildInputs = [ tls ] ++ oa.buildInputs;
    propagatedBuildInputs = buildInputs;
    minimumOCamlVersion = "4.07";
  });
  conduit-lwt-unix = osuper.conduit-lwt-unix.versions."2.0.2";
  cohttp-lwt-unix = osuper.cohttp-lwt-unix.versions."2.4.0";
  cohttp-lwt = osuper.cohttp-lwt.versions."2.4.0";
  macaddr = osuper.macaddr.versions."4.0.0".overrideAttrs (_: {
    minimumOCamlVersion = "4.07";
  });

  lwt = osuper.lwt.versions."4.2.1";

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
    osuper.tezos-node.overrideAttrs (o: rec {
      postInstall = "rm $bin/*.sh";
    });
}
