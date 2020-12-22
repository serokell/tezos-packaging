# SPDX-FileCopyrightText: 2019 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ

# This file needs to become empty.
self: super: oself: osuper:
with oself;
# external rust libraries
let
  rustc-bls12-381 = self.rustPlatform.buildRustPackage rec {
    pname = "rustc-bls12-381";
    version = "0.7.2";
    RUSTFLAGS = "-C target-feature=-crt-static -C lto=off";
    src = builtins.fetchTarball {
      url = "https://gitlab.com/dannywillems/rustc-bls12-381/-/archive/0.7.2/rustc-bls12-381-0.7.2.tar.gz";
    };
    cargoSha256 = "1wdapzy2qk7ml17sihls3pykj740spzrm8mbvh4495wq5r07v2gr";
    cargoPatches = [
      # a patch file to add Cargo.lock in the source code
      ./bls12-381-add-Cargo.lock.patch
    ];
  };
  librustzcash = self.rustPlatform.buildRustPackage rec {
    pname = "librustzcash";
    version = "0.1.0";
    RUSTFLAGS = "-C target-feature=-crt-static -C lto=off";
    src = builtins.fetchTarball {
      url = "https://github.com/zcash/librustzcash/archive/0.1.0.tar.gz";
    };
    cargoSha256 = "1wzyrcmcbrna6rjzw19c4lq30didzk4w6fs6wmvxp0xfg4qqdlax";
  };
  zcash-params = import ./zcash.nix {};
  zcash-post-fixup = pkg: ''
    mv $bin/${pkg.name} $bin/${pkg.name}-wrapped
    makeWrapper $bin/${pkg.name}-wrapped $bin/${pkg.name} --prefix XDG_DATA_DIRS : ${zcash-params}
  '';
in
rec {
  ocaml = self.ocaml-ng.ocamlPackages_4_09.ocaml.overrideAttrs (o: o // {
    hardeningDisable = o.hardeningDisable ++
                       self.stdenv.lib.optional self.stdenv.hostPlatform.isMusl "pie";
  });
  # FIXME opam-nix needs to do this
  ocamlfind = findlib;

  ocamlgraph = osuper.ocamlgraph.override (_: { gtkSupport = false; });

  # FIXME opam-nix needs to do version resolution
  ezjsonm = osuper.ezjsonm.versions."1.2.0";
  hacl-star-raw = osuper.hacl-star-raw.overrideAttrs (o: rec {
    preConfigure = "patchShebangs raw/configure";
    sourceRoot = ".";
    buildInputs = o.buildInputs ++ [ self.which ];
    propagatedBuildInputs = buildInputs;
  });
  hacl-star = osuper.hacl-star.overrideAttrs (_: rec {
    sourceRoot = ".";
  });
  irmin = osuper.irmin.versions."2.2.0";
  irmin-pack = osuper.irmin-pack.versions."2.2.0".overrideAttrs (o : rec {
    buildInputs = o.buildInputs ++ [ alcotest-lwt ];
    propagatedBuildInputs = buildInputs;
  });
  pcre = osuper.pcre.overrideAttrs (o: rec {
    buildInputs = o.buildInputs ++ [ odoc ];
    propagatedBuildInputs = buildInputs;
  });

  bls12-381 = osuper.bls12-381.overrideAttrs (o:
    rec {
      buildInputs = o.buildInputs ++ [ rustc-bls12-381 ];
      buildPhase = ''
        cp ${rustc-bls12-381.src}/include/* src/
      '' + o.buildPhase;
  });

  tezos-sapling = osuper.tezos-sapling.overrideAttrs (o:
    let extern-C-patch = ./librustzcash-extern-C.patch; in
    rec {
      buildInputs = o.buildInputs ++ [ librustzcash rustc-bls12-381 self.gcc self.git ];
      buildPhase = ''
        cp ${librustzcash.src}/librustzcash/include/librustzcash.h .
        patch librustzcash.h ${extern-C-patch}
      '' + o.buildPhase;
    }
  );
  zarith = osuper.zarith.overrideAttrs(_ : {
    version = "1.10";
    src = self.fetchurl {
      url = "https://github.com/ocaml/Zarith/archive/release-1.10.tar.gz";
      sha256 = "1qxrl0v2mk9wghc1iix3n0vfz2jbg6k5wpn1z7p02m2sqskb0zhb";
    };
  });

  # FIXME opam-nix needs to handle "external" (native) dependencies correctly
  conf-gmp = self.gmp;
  conf-libev = self.libev;
  conf-hidapi = self.hidapi;
  conf-pkg-config = self.pkg-config;
  conf-libffi = self.libffi;
  conf-which = null;
  conf-rust = self.cargo;
  conf-libpcre = self.pcre;
  conf-perl = self.perl;
  ctypes-foreign = oself.ctypes;

  # FIXME X11 in nixpkgs musl
  lablgtk = null;

  # FIXME recursive dependencies WTF
  bigstring = osuper.bigstring.overrideAttrs (_: { doCheck = false; });

  tezos-protocol-environment = osuper.tezos-protocol-environment.overrideAttrs (o: rec {
    buildInputs = o.buildInputs ++ [ zarith ];
    propagatedBuildInputs = buildInputs;
  });

  # FIXME dependencies in tezos-protocol-compiler.opam
  tezos-protocol-compiler = osuper.tezos-protocol-compiler.overrideAttrs
    (oa: rec {
      buildInputs = oa.buildInputs ++ [ oself.pprint rustc-bls12-381 ];
      propagatedBuildInputs = buildInputs;
    });

  # packages depend on rust library
  tezos-validator = osuper.tezos-validator.overrideAttrs
    (o: rec {
      buildInputs = o.buildInputs ++ [ librustzcash ];
    });
  tezos-protocol-006-PsCARTHA-parameters = osuper.tezos-protocol-006-PsCARTHA-parameters.overrideAttrs
    (o: rec {
      buildInputs = o.buildInputs ++ [ librustzcash ];
      XDG_DATA_DIRS = "${zcash-params}:$XDG_DATA_DIRS";
    });
  tezos-protocol-007-PsDELPH1-parameters = osuper.tezos-protocol-007-PsDELPH1-parameters.overrideAttrs
    (o: rec {
      buildInputs = o.buildInputs ++ [ librustzcash ];
      XDG_DATA_DIRS = "${zcash-params}:$XDG_DATA_DIRS";
    });
  tezos-protocol-008-PtEdoTez-parameters = osuper.tezos-protocol-008-PtEdoTez-parameters.overrideAttrs
    (o: rec {
      buildInputs = o.buildInputs ++ [ librustzcash ];
      XDG_DATA_DIRS = "${zcash-params}:$XDG_DATA_DIRS";
    });

  # FIXME apply this patch upstream
  tezos-stdlib-unix = osuper.tezos-stdlib-unix.overrideAttrs
    (_: { patches = [ ./stdlib-unix.patch ]; });

  tezos-client = osuper.tezos-client.overrideAttrs
    (o: {
      buildInputs = o.buildInputs ++ [ librustzcash self.makeWrapper ];
      postInstall = "rm $bin/tezos-admin-client $bin/*.sh";
      postFixup = zcash-post-fixup o;
    });

  tezos-accuser-007-PsDELPH1 = osuper.tezos-accuser-007-PsDELPH1.overrideAttrs
    (o: {
      buildInputs = o.buildInputs ++ [ librustzcash self.makeWrapper ];
      postFixup = zcash-post-fixup o;
    });
  tezos-baker-007-PsDELPH1 = osuper.tezos-baker-007-PsDELPH1.overrideAttrs
    (o: {
      buildInputs = o.buildInputs ++ [ librustzcash self.makeWrapper ];
      postFixup = zcash-post-fixup o;
    });
  tezos-endorser-007-PsDELPH1 = osuper.tezos-endorser-007-PsDELPH1.overrideAttrs
    (o: {
      buildInputs = o.buildInputs ++ [ librustzcash self.makeWrapper ];
      postFixup = zcash-post-fixup o;
    });
  tezos-accuser-008-PtEdoTez = osuper.tezos-accuser-008-PtEdoTez.overrideAttrs
    (o: {
      buildInputs = o.buildInputs ++ [ librustzcash self.makeWrapper ];
      postFixup = zcash-post-fixup o;
    });
  tezos-baker-008-PtEdoTez = osuper.tezos-baker-008-PtEdoTez.overrideAttrs
    (o: {
      buildInputs = o.buildInputs ++ [ librustzcash self.makeWrapper ];
      postFixup = zcash-post-fixup o;
    });
  tezos-endorser-008-PtEdoTez = osuper.tezos-endorser-008-PtEdoTez.overrideAttrs
    (o: {
      buildInputs = o.buildInputs ++ [ librustzcash self.makeWrapper ];
      postFixup = zcash-post-fixup o;
    });
  tezos-codec = osuper.tezos-codec.overrideAttrs
    (o: {
      buildInputs = o.buildInputs ++ [ rustc-bls12-381 librustzcash self.makeWrapper ];
      postFixup = zcash-post-fixup o;
    });
  tezos-signer = osuper.tezos-signer.overrideAttrs
    (o: {
      buildInputs = o.buildInputs ++ [ rustc-bls12-381 librustzcash self.makeWrapper ];
      postFixup = zcash-post-fixup o;
    });

  tezos-admin-client = (osuper.tezos-client.overrideAttrs (o: {
    buildInputs = o.buildInputs ++ [ librustzcash ];
    name = "tezos-admin-client";
    postInstall = "rm $bin/tezos-client $bin/*.sh";
  })).overrideAttrs (o: {
    buildInputs = o.buildInputs ++ [self.makeWrapper ];
    postFixup = zcash-post-fixup o;
  });

  tezos-node =
    osuper.tezos-node.overrideAttrs (o: rec {
      buildInputs = o.buildInputs ++ [ librustzcash self.makeWrapper ];
      postInstall = "rm $bin/*.sh";
      postFixup = zcash-post-fixup o;
    });
}
