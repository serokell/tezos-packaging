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
  sources = import ../nix/sources.nix;
  inherit (import "${sources.crate2nix}/tools.nix" { pkgs = self; }) generatedCargoNix;
  librustzcash = (self.callPackage (generatedCargoNix rec {
    name = "librustzcash";
    src = self.fetchzip {
      url =
        "https://github.com/zcash/zcash/archive/8c778c9c0d9f3c91650f02d0becaacac24e61108.tar.gz";
      sha256 = "sha256-EHX8MHQZG3dTnHV2J2vFbDlurV8pNYggxTYLOyUT/yY=";
    };
  }) {
    defaultCrateOverrides = self.defaultCrateOverrides // {
      librustzcash = oa: {
        postBuild = "build_lib src/rust/src/rustzcash.rs";
        postInstall = ''
          mkdir -p $out/lib
          cp -r $lib/lib/*.a $out/lib/librustzcash.a
        '';
        extraRustcOpts = ["-C lto=off"];
      };
    };
  }).rootCrate.build;
  zcash-params = import ./zcash.nix {};
  zcash-post-fixup = pkg: ''
    mv $bin/${pkg.name} $bin/${pkg.name}-wrapped
    makeWrapper $bin/${pkg.name}-wrapped $bin/${pkg.name} --prefix XDG_DATA_DIRS : ${zcash-params}
  '';
in
rec {
  ocaml = self.ocaml-ng.ocamlPackages_4_10.ocaml;
  dune = self.ocamlPackages.dune_2;
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
  index = osuper.index.versions."1.3.1";
  irmin = osuper.irmin.versions."2.5.4";
  irmin-pack = osuper.irmin-pack.versions."2.5.4";
  irmin-layers = osuper.irmin-layers.versions."2.5.4";
  pcre = osuper.pcre.overrideAttrs (o: rec {
    buildInputs = o.buildInputs ++ [ odoc ];
    propagatedBuildInputs = buildInputs;
  });

  data-encoding = osuper.data-encoding.versions."0.3";
  json-data-encoding = osuper.json-data-encoding.versions."0.9.1";
  json-data-encoding-bson = osuper.json-data-encoding-bson.versions."0.9.1";
  ff = osuper.ff.versions."0.4.0";
  bls12-381 = osuper.bls12-381.overrideAttrs (o:
    rec {
      buildInputs = o.buildInputs ++ [ rustc-bls12-381 ];
      buildPhase = ''
        cp ${rustc-bls12-381.src}/include/* src/
      '' + o.buildPhase;
  });

  tezos-sapling = osuper.tezos-sapling.overrideAttrs (o:
    rec {
      buildInputs = o.buildInputs ++ [ librustzcash rustc-bls12-381 self.gcc self.git ];
      buildPhase = ''
        cp ${librustzcash.src}/src/rust/include/librustzcash.h .
      '' + o.buildPhase;
    }
  );
  zarith = osuper.zarith.overrideAttrs(o : {
    version = "1.10";
    buildInputs = o.buildInputs ++ [self.perl];
    src = self.fetchurl {
      url = "https://github.com/ocaml/Zarith/archive/release-1.10.tar.gz";
      sha256 = "1qxrl0v2mk9wghc1iix3n0vfz2jbg6k5wpn1z7p02m2sqskb0zhb";
    };
    patchPhase = "patchShebangs ./z_pp.pl";
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
  conf-m4 = self.m4;
  ctypes-foreign = ctypes;
  gmp = self.gmp;

  ctypes = osuper.ctypes.versions."0.17.1".overrideAttrs (o: rec{
    pname = "ctypes";
    buildInputs = o.buildInputs ++ [ self.libffi ];
    src = self.fetchurl {
      url = "https://github.com/ocamllabs/ocaml-ctypes/archive/0.17.1.tar.gz";
      sha256 = "sha256-QWc8Lrk8qZ7T3hg77z5rQ2xnoNkCsRC+XaFYqtkip+k=";
    };
    installPhase = ''
      runHook preInstall
      mkdir -p $OCAMLFIND_DESTDIR
      "make" "install"
      if [[ -d $OCAMLFIND_DESTDIR/${pname} ]]; then mv $OCAMLFIND_DESTDIR/${pname} $lib; ln -s $lib $OCAMLFIND_DESTDIR/${pname}; else touch $lib; fi
      if [[ -d $out/bin ]]; then mv $out/bin $bin; ln -s $bin $out/bin; else touch $bin; fi
      if [[ -d $out/share ]]; then mv $out/share $share; ln -s $share $out/share; else touch $share; fi
      runHook postInstall
    '';
  });

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
  tezos-protocol-008-PtEdo2Zk-parameters = osuper.tezos-protocol-008-PtEdo2Zk-parameters.overrideAttrs
    (o: rec {
      buildInputs = o.buildInputs ++ [ librustzcash ];
      XDG_DATA_DIRS = "${zcash-params}:$XDG_DATA_DIRS";
    });
  tezos-protocol-009-PsFLorBA-parameters = osuper.tezos-protocol-009-PsFLorBA-parameters.overrideAttrs
    (o: rec {
      buildInputs = o.buildInputs ++ [ librustzcash ];
      XDG_DATA_DIRS = "${zcash-params}:$XDG_DATA_DIRS";
    });
  tezos-protocol-009-PsFLoren-parameters = osuper.tezos-protocol-009-PsFLoren-parameters.overrideAttrs
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

  tezos-accuser-009-PsFLoren = osuper.tezos-accuser-009-PsFLoren.overrideAttrs
    (o: {
      buildInputs = o.buildInputs ++ [ librustzcash self.makeWrapper ];
      postFixup = zcash-post-fixup o;
    });
  tezos-baker-009-PsFLoren = osuper.tezos-baker-009-PsFLoren.overrideAttrs
    (o: {
      buildInputs = o.buildInputs ++ [ librustzcash self.makeWrapper ];
      postFixup = zcash-post-fixup o;
    });
  tezos-endorser-009-PsFLoren = osuper.tezos-endorser-009-PsFLoren.overrideAttrs
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
