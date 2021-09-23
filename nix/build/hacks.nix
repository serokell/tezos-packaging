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
  ocaml = self.ocaml-ng.ocamlPackages_4_12.ocaml;
  dune = self.ocamlPackages.dune_2;
  # FIXME opam-nix needs to do this
  ocamlfind = findlib;

  # FIXME opam-nix needs to do version resolution
  ezjsonm = osuper.ezjsonm.versions."1.2.0";
  hacl-star-raw = osuper.hacl-star-raw.versions."0.3.2".overrideAttrs (o: rec {
    preConfigure = "patchShebangs raw/configure";
    sourceRoot = ".";
    buildInputs = o.buildInputs ++ [ self.which ];
    propagatedBuildInputs = buildInputs;
    minimalOCamlVersion = "4.10";
  });
  hacl-star = osuper.hacl-star.versions."0.3.2".overrideAttrs (_: rec {
    sourceRoot = ".";
  });
  optint = osuper.optint.versions."0.1.0";
  repr = osuper.repr.overrideAttrs (o: rec {
    version = "0.4.0";
    src = self.fetchurl {
      url = "https://github.com/mirage/${o.pname}/releases/download/${version}/${o.pname}-fuzz-${version}.tbz";
      sha256 = "1kpwgncyxcrq90dn7ilja7c5i88whc3fz4fmq1lwr0ar95d7d48p";
    };
  });
  ppx_repr = osuper.ppx_repr.overrideAttrs (_: {
    doCheck = false;
  });
  terminal = osuper.terminal.versions."0.2.1".overrideAttrs (o: {
    buildPhase = ''
      runHook preBuild
      "dune" "build" "-p" "${o.pname}" "-j" "$NIX_BUILD_CORES"
      runHook postBuild
    '';
  });
  progress = osuper.progress.versions."0.2.1".overrideAttrs (o: {
    buildPhase = ''
      runHook preBuild
      "dune" "build" "-p" "${o.pname}" "-j" "$NIX_BUILD_CORES"
      runHook postBuild
    '';
  });
  index = osuper.index.versions."1.4.1";
  ppx_irmin = osuper.ppx_irmin.versions."2.7.2";
  irmin = osuper.irmin.versions."2.7.2";
  irmin-pack = osuper.irmin-pack.versions."2.7.2";
  irmin-layers = osuper.irmin-layers.versions."2.7.2";

  lwt-canceler = osuper.lwt-canceler.versions."0.3";

  benchmark = osuper.benchmark.overrideAttrs (_: {
    doCheck = false;
  });

  data-encoding = osuper.data-encoding.versions."0.3";
  json-data-encoding = osuper.json-data-encoding.versions."0.9.1";
  json-data-encoding-bson = osuper.json-data-encoding-bson.versions."0.9.1";
  ff = osuper.ff.versions."0.4.0";

  bls12-381-gen = osuper.bls12-381-gen.versions."0.4.3";
  bls12-381 = osuper.bls12-381.versions."0.4.3".overrideAttrs (o:
    rec {
      buildInputs = o.buildInputs ++ [ rustc-bls12-381 ];
      buildPhase = ''
        cp ${rustc-bls12-381.src}/include/* src/
      '' + o.buildPhase;
  });

  bls12-381-unix = osuper.bls12-381-unix.versions."0.4.3".overrideAttrs (o:
    rec {
      buildInputs = o.buildInputs ++ [ rustc-bls12-381 ];
      buildPhase = ''
        cp ${rustc-bls12-381.src}/include/* src/unix/
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
  conf-zlib = self.zlib;
  ctypes-foreign = ctypes;
  gmp = self.gmp;

  zlib = osuper.zlib.overrideAttrs (o: {
    src = self.fetchurl {
      url = "	https://github.com/madroach/ocaml-zlib/archive/0.6.tar.gz";
      sha256 = "sha256-QWc8Lrk8qZ7T3hg77z5rQ2xnoNkCsRC+XaFXqtkip+k=";
    };
  });
  camlzip = osuper.camlzip.versions."1.10".overrideAttrs (_: {
    src = self.fetchzip {
      url = "https://github.com/xavierleroy/camlzip/archive/rel110.zip";
      sha256 = "1pm1vs947cbb4b4827pcz5kbj41miyxw599craznwm1ix27bmpj6";
    };
  });

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

  tezos-client-base-unix = osuper.tezos-client-base-unix.overrideAttrs (o: rec {
    buildInputs = o.buildInputs ++
      [ lwt-exit tezos-shell-services tezos-signer-backends tezos-proxy
        tezos-mockup-commands
      ];
    propagatedBuildInputs = buildInputs;
  });

  # FIXME dependencies in tezos-protocol-compiler.opam
  tezos-protocol-compiler = osuper.tezos-protocol-compiler.overrideAttrs
    (oa: rec {
      buildInputs = oa.buildInputs ++
        [ oself.pprint rustc-bls12-381 tezos-stdlib-unix ocp-ocamlres tezos-protocol-environment-sigs
          tezos-base re tezos-version
        ];
      propagatedBuildInputs = buildInputs;
    });

  tezos-rust-libs = osuper.tezos-rust-libs.overrideAttrs (_: {
    src = self.fetchzip {
      url = "https://gitlab.com/tezos/tezos-rust-libs/-/archive/v1.1/tezos-rust-libs-v1.1.zip";
      sha256 = "08wpcq6cbdvxdhazcpqzz4pywagy3fdbys07q2anbk6lq45rc2w6";
    };
  });

  tezos-crypto = osuper.tezos-crypto.overrideAttrs (o: rec {
    buildInputs = o.buildInputs ++ [ bls12-381 ];
    propagatedBuildInputs = buildInputs;
  });

  tezos-protocol-alpha = osuper.tezos-protocol-alpha.overrideAttrs (o : {
    buildInputs = o.buildInputs ++ [ tezos-protocol-environment ];
  });
  tezos-protocol-000-Ps9mPmXa = osuper.tezos-protocol-000-Ps9mPmXa.overrideAttrs (o : {
    buildInputs = o.buildInputs ++ [ tezos-protocol-environment ];
  });
  tezos-protocol-001-PtCJ7pwo = osuper.tezos-protocol-001-PtCJ7pwo.overrideAttrs (o : {
    buildInputs = o.buildInputs ++ [ tezos-protocol-environment ];
  });
  tezos-protocol-002-PsYLVpVv = osuper.tezos-protocol-002-PsYLVpVv.overrideAttrs (o : {
    buildInputs = o.buildInputs ++ [ tezos-protocol-environment ];
  });
  tezos-protocol-003-PsddFKi3 = osuper.tezos-protocol-003-PsddFKi3.overrideAttrs (o : {
    buildInputs = o.buildInputs ++ [ tezos-protocol-environment ];
  });
  tezos-protocol-004-Pt24m4xi = osuper.tezos-protocol-004-Pt24m4xi.overrideAttrs (o : {
    buildInputs = o.buildInputs ++ [ tezos-protocol-environment ];
  });
  tezos-protocol-005-PsBABY5H = osuper.tezos-protocol-005-PsBABY5H.overrideAttrs (o : {
    buildInputs = o.buildInputs ++ [ tezos-protocol-environment ];
  });
  tezos-protocol-005-PsBabyM1 = osuper.tezos-protocol-005-PsBabyM1.overrideAttrs (o : {
    buildInputs = o.buildInputs ++ [ tezos-protocol-environment ];
  });
  tezos-protocol-006-PsCARTHA = osuper.tezos-protocol-006-PsCARTHA.overrideAttrs (o : {
    buildInputs = o.buildInputs ++ [ tezos-protocol-environment ];
  });
  tezos-protocol-007-PsDELPH1 = osuper.tezos-protocol-007-PsDELPH1.overrideAttrs (o : {
    buildInputs = o.buildInputs ++ [ tezos-protocol-environment ];
  });
  tezos-protocol-008-PtEdo2Zk = osuper.tezos-protocol-008-PtEdo2Zk.overrideAttrs (o : {
    buildInputs = o.buildInputs ++ [ tezos-protocol-environment ];
  });
  tezos-protocol-009-PsFLoren = osuper.tezos-protocol-009-PsFLoren.overrideAttrs (o : {
    buildInputs = o.buildInputs ++ [ tezos-protocol-environment ];
  });
  tezos-protocol-009-PsFLorBA = osuper.tezos-protocol-009-PsFLorBA.overrideAttrs (o : {
    buildInputs = o.buildInputs ++ [ tezos-protocol-environment ];
  });
  tezos-protocol-010-PtGRANAD = osuper.tezos-protocol-010-PtGRANAD.overrideAttrs (o : {
    buildInputs = o.buildInputs ++ [ tezos-protocol-environment ];
  });
  tezos-protocol-demo-noops = osuper.tezos-protocol-demo-noops.overrideAttrs (o : {
    buildInputs = o.buildInputs ++ [ tezos-protocol-environment ];
  });
  tezos-protocol-genesis-carthagenet = osuper.tezos-protocol-genesis-carthagenet.overrideAttrs (o : {
    buildInputs = o.buildInputs ++ [ tezos-protocol-environment ];
  });
  tezos-protocol-genesis = osuper.tezos-protocol-genesis.overrideAttrs (o : {
    buildInputs = o.buildInputs ++ [ tezos-protocol-environment ];
  });
  tezos-protocol-plugin-alpha = osuper.tezos-protocol-plugin-alpha.overrideAttrs (o : {
    buildInputs = o.buildInputs ++ [ tezos-protocol-environment ];
  });
  tezos-protocol-plugin-007-PsDELPH1 = osuper.tezos-protocol-plugin-007-PsDELPH1.overrideAttrs (o : {
    buildInputs = o.buildInputs ++ [ tezos-protocol-environment ];
  });
  tezos-protocol-plugin-008-PtEdo2Zk = osuper.tezos-protocol-plugin-008-PtEdo2Zk.overrideAttrs (o : {
    buildInputs = o.buildInputs ++ [ tezos-protocol-environment ];
  });
  tezos-protocol-plugin-009-PsFLoren = osuper.tezos-protocol-plugin-009-PsFLoren.overrideAttrs (o : {
    buildInputs = o.buildInputs ++ [ tezos-protocol-environment ];
  });
  tezos-protocol-plugin-010-PtGRANAD = osuper.tezos-protocol-plugin-010-PtGRANAD.overrideAttrs (o : {
    buildInputs = o.buildInputs ++ [ tezos-protocol-environment ];
  });

  # packages depend on rust library
  tezos-validator = osuper.tezos-validator.overrideAttrs
    (o: rec {
      buildInputs = o.buildInputs ++ [ librustzcash ];
    });
  tezos-protocol-alpha-parameters = osuper.tezos-protocol-alpha-parameters.overrideAttrs
    (o: rec {
      buildInputs = o.buildInputs ++ [ librustzcash ];
      XDG_DATA_DIRS = "${zcash-params}:$XDG_DATA_DIRS";
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
  tezos-protocol-010-PtGRANAD-parameters = osuper.tezos-protocol-010-PtGRANAD-parameters.overrideAttrs
    (o: rec {
      buildInputs = o.buildInputs ++ [ librustzcash ];
      XDG_DATA_DIRS = "${zcash-params}:$XDG_DATA_DIRS";
    });

  # FIXME apply this patch upstream
  tezos-stdlib-unix = osuper.tezos-stdlib-unix.overrideAttrs
    (_: { patches = [ ./stdlib-unix.patch ]; });

  tezos-client = osuper.tezos-client.overrideAttrs
    (o: {
      buildInputs = o.buildInputs ++ [ librustzcash self.makeWrapper tezos-client-alpha-commands-registration ];
      postInstall = "rm $bin/tezos-admin-client $bin/*.sh";
      postFixup = zcash-post-fixup o;
    });

  tezos-accuser-010-PtGRANAD = osuper.tezos-accuser-010-PtGRANAD.overrideAttrs
    (o: {
      buildInputs = o.buildInputs ++ [ librustzcash self.makeWrapper ];
      postFixup = zcash-post-fixup o;
    });
  tezos-baker-010-PtGRANAD = osuper.tezos-baker-010-PtGRANAD.overrideAttrs
    (o: {
      buildInputs = o.buildInputs ++ [ librustzcash self.makeWrapper ];
      postFixup = zcash-post-fixup o;
    });
  tezos-endorser-010-PtGRANAD = osuper.tezos-endorser-010-PtGRANAD.overrideAttrs
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
