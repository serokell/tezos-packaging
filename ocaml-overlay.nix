# SPDX-FileCopyrightText: 2019 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: MPL-2.0

{ sources ? import ./nix/sources.nix
, protocols ? builtins.fromJSON (builtins.readFile ./protocols.json)
, pkgs ? import sources.nixpkgs { }
, opam-nix ? import sources.opam-nix pkgs
}:
self: super:
{
  ocamlPackages = self.ocaml-ng.ocamlPackages_4_09.overrideScope'
    (builtins.foldl' self.lib.composeExtensions (_: _: { }) [
      (opam-nix.traverseOPAMRepo' sources.opam-repository)
      (oself: osuper: { index-super = osuper.index.versions."1.2.0"; })
      (opam-nix.callOPAMPackage sources.tezos)
      (_: # Nullify all the ignored protocols so that we don't build them
        builtins.mapAttrs (name: pkg:
          if builtins.any
          (proto: !isNull (builtins.match "tezos.*${proto}.*" name))
          protocols.ignored then
            null
          else
            pkg))
      (oself: osuper:
        with oself; {
          ocamlfind = findlib;
          lablgtk = null;
          lwt = lwt4;
          bigstring = osuper.bigstring.overrideAttrs (_: { doCheck = false; });
          xmldiff =
            osuper.xmldiff.overrideAttrs (_: { src = sources.xmldiff; });
          index = oself.index-super;
          ezjsonm = osuper.ezjsonm.versions."1.1.0";
          ipaddr = osuper.ipaddr.versions."4.0.0";
          conduit = osuper.conduit.versions."2.1.0";
          conduit-lwt-unix = osuper.conduit-lwt-unix.versions."2.0.2";
          cohttp-lwt-unix = osuper.cohttp-lwt-unix.versions."2.4.0";
          cohttp-lwt = osuper.cohttp-lwt.versions."2.4.0";
          macaddr = osuper.macaddr.versions."4.0.0";
          base-unix = oself.base;
          conf-gmp = self.gmp;
          conf-libev = self.libev;
          conf-hidapi = self.hidapi;
          conf-pkg-config = self.pkg-config;
          tezos-protocol-compiler = osuper.tezos-protocol-compiler.overrideAttrs
            (oa: rec {
              buildInputs = oa.buildInputs ++ [ oself.pprint ];
              propagatedBuildInputs = buildInputs;
              outputs = [ "out" "lib" ];
              postInstall = "cp -Lr $out/lib/ocaml/${oself.ocaml.version}/site-lib/tezos-protocol-compiler $lib";
            });
          tezos-stdlib-unix = osuper.tezos-stdlib-unix.overrideAttrs
            (_: { patches = [ ./stdlib-unix.patch ]; });
        })
        (opam-nix.cacheSources sources)
    ]);
}
