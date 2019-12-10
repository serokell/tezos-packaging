# SPDX-FileCopyrightText: 2019 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: MPL-2.0
{ pkgs ? import <nixpkgs> { } }:
branchInfo:

let
  oca = pkgs.ocaml-ng.ocamlPackages_4_07.overrideScope' (self: super: {
    bigstring = self.callPackage
      ({ stdenv, fetchFromGitHub, buildDunePackage, base }:

        buildDunePackage rec {
          pname = "bigstring";
          version = "0.2";

          minimumOCamlVersion = "4.03";

          src = fetchFromGitHub {
            owner = "c-cube";
            repo = "ocaml-${pname}";
            rev = version;
            sha256 = "0ypdf29cmwmjm3djr5ygz8ls81dl41a4iz1xx5gbcdpbrdiapb77";
          };

          buildInputs = [ base ];
          doCheck = true;
        }) { };
    nonstd = self.callPackage ({ stdenv, fetchgit, buildDunePackage, base }:

      buildDunePackage rec {
        pname = "nonstd";
        version = "0.0.3";

        minimumOCamlVersion = "4.03";

        src = fetchgit {
          url = "https://bitbucket.org/smondet/nonstd.git";
          rev = "${pname}.${version}";
          sha256 = "0ccjwcriwm8fv29ij1cnbc9win054kb6pfga3ygzdbjpjb778j46";
        };
        #doCheck = true;
      }) { };
    sosa = self.callPackage
      ({ stdenv, fetchFromGitHub, buildDunePackage, ocamlbuild }:

        buildDunePackage rec {
          pname = "sosa";
          version = "0.3.0";

          minimumOCamlVersion = "4.03";

          src = fetchFromGitHub {
            owner = "hammerlab";
            repo = "${pname}";
            rev = "${pname}.${version}";
            sha256 = "053hdv6ww0q4mivajj4iyp7krfvgq8zajq9d8x4mia4lid7j0dyk";
          };

          buildInputs = [ ocamlbuild ];
          buildPhase = "make build";
          installPhase = ''
            mkdir -p $out/lib/ocaml/4.07.1/site-lib
            make install
          '';
          doCheck = false;
        }) { };
    genspio = self.callPackage
      ({ stdenv, fetchFromGitHub, buildDunePackage, nonstd, sosa, base }:

        buildDunePackage rec {
          pname = "genspio";
          version = "0.0.2";

          minimumOCamlVersion = "4.03";

          src = fetchFromGitHub {
            owner = "hammerlab";
            repo = "${pname}";
            rev = "genspio.${version}";
            sha256 = "0cp6p1f713sfv4p2r03bzvjvakzn4ili7hf3a952b3w1k39hv37x";
          };
          propagatedBuildInputs = [ nonstd sosa ];
          configurePhase = "ocaml please.mlt configure";
          doCheck = false;
        }) { };
    dum = self.callPackage
      ({ stdenv, fetchFromGitHub, buildDunePackage, easy-format }:

        buildDunePackage rec {
          pname = "dum";
          version = "1.0.1";

          minimumOCamlVersion = "4.03";
          buildPhase = "";
          installPhase = ''
            mkdir -p $out/lib/ocaml/4.07.1/site-lib
            make install
          '';

          src = fetchFromGitHub {
            owner = "mjambon";
            repo = "${pname}";
            rev = "v${version}";
            sha256 = "0yrxl97szjc0s2ghngs346x3y0xszx2chidgzxk93frjjpsr1mlr";
          };

          buildInputs = [ easy-format ];
          doCheck = false;
        }) { };
    hidapi = self.callPackage ({ stdenv, fetchFromGitHub, buildDunePackage
      , hidapi, bigstring, pkg-config }:

      buildDunePackage rec {
        pname = "hidapi";
        version = "1.1.1";

        minimumOCamlVersion = "4.03";

        src = fetchFromGitHub {
          owner = "vbmithr";
          repo = "ocaml-${pname}";
          rev = version;
          sha256 = "1qhc8iby3i54zflbi3yrnhpg62pwdl6g2sfnykgashjy7ghh495y";
        };

        buildInputs = [ bigstring hidapi pkg-config ];
        doCheck = true;
      }) { hidapi = pkgs.hidapi; };
    ocamlgraph = self.callPackage
      ({ stdenv, fetchFromGitHub, buildDunePackage }:

        buildDunePackage rec {
          pname = "ocamlgraph";
          version = "1.8.8";

          minimumOCamlmVersion = "4.03";

          src = builtins.fetchTarball {
            url = "http://ocamlgraph.lri.fr/download/ocamlgraph-1.8.8.tar.gz";
            sha256 = "0xly2ckq9wy8pkszppcqv1bqb2yl2arij8f6n07bfiyaxh22crpq";
          };
          buildPhase = ''
            chmod +x configure
            ./configure
            make
          '';
          installPhase = ''
            mkdir -p $out/lib/ocaml/4.07.1/site-lib
            make install-findlib
          '';

          buildInputs = [ ];
          propagatedBuildInputs = [ ];
          doCheck = false;
        }) { };
    irmin = self.callPackage ({ stdenv, fetchFromGitHub, buildDunePackage, fmt
      , uri, jsonm, lwt4, logs, base64, digestif, ocamlgraph, astring, hex
      , alcotest }:

      buildDunePackage rec {
        pname = "irmin";
        version = "1.4.0";

        minimumOCamlVersion = "4.03";

        src = fetchFromGitHub {
          owner = "mirage";
          repo = pname;
          rev = version;
          sha256 = "0f272h9d0hs0wn5m30348wx7vz7524yk40wx5lx895vv3r3p7q7c";
        };
        buildInputs = [ fmt uri jsonm lwt4 base64 logs astring hex alcotest ];
        propagatedBuildInputs = [ ocamlgraph digestif ];
        doCheck = true;
      }) { };

    ipaddr = super.ipaddr.overrideDerivation (o: rec {
      version = "4.0.0";
      src = pkgs.fetchFromGitHub {
        owner = "mirage";
        repo = "ocaml-${o.pname}";
        rev = "v${version}";
        sha256 = "1ywhabdji7hqrmr07dcxlsxf5zndagrdxx378csi5bv3c5n9547z";
      };
      buildPhase = "dune build -p ipaddr,macaddr,ipaddr-sexp";
      propagatedBuildInputs = o.propagatedBuildInputs ++ [ self.domain-name ];
    });
    conduit = super.conduit.overrideDerivation (o: rec {
      version = "2.0.1";
      src = pkgs.fetchFromGitHub {
        owner = "mirage";
        repo = "ocaml-${o.pname}";
        rev = "v${version}";
        sha256 = "0v4lxc6g9mavx8nk7djzsvx1blw5wsjn2cg6k6a35fyv64xmwd73";
      };
      propagatedBuildInputs = o.propagatedBuildInputs ++ [ self.sexplib ];
    });
    conduit-lwt-unix = super.conduit-lwt-unix.overrideDerivation (o: rec {
      version = "2.0.1";
      src = pkgs.fetchFromGitHub {
        owner = "mirage";
        repo = "ocaml-conduit";
        rev = "v${version}";
        sha256 = "0v4lxc6g9mavx8nk7djzsvx1blw5wsjn2cg6k6a35fyv64xmwd73";
      };
      propagatedBuildInputs = [ self.conduit-lwt self.logs self.tls ];
    });
    cohttp = super.cohttp.overrideDerivation (o: rec {
      version = "2.3.0";
      name = "cohttp-2.3.0";
      src = pkgs.fetchFromGitHub {
        owner = "mirage";
        repo = "ocaml-${o.pname}";
        rev = "v${version}";
        sha256 = "0fag9zhv1lhbq1p4p1cmbav009x2d79kq3iv04pisj5y071qhhvr";
      };
      propagatedBuildInputs = o.propagatedBuildInputs ++ [ self.stdlib-shims ];
    });
    domain-name = self.callPackage
      ({ stdenv, fetchFromGitHub, buildDunePackage, fmt, astring }:
        buildDunePackage rec {
          pname = "domain-name";
          version = "0.3.0";
          src = pkgs.fetchFromGitHub {
            owner = "hannesm";
            repo = "${pname}";
            rev = "v${version}";
            sha256 = "06l82k27wa446k0sd799i73rrqwwmqfm542blkx6bbm2xpxaz2cm";
          };
          propagatedBuildInputs = [ fmt astring ];
        }) { };
    pprint = self.callPackage
      ({ stdenv, fetchFromGitHub, buildDunePackage, ocamlbuild }:
        buildDunePackage rec {
          pname = "pprint";
          version = "20180528";

          minimumOCamlVersion = "4.03";
          src = fetchFromGitHub {
            owner = "fpottier";
            repo = "${pname}";
            rev = "${version}";
            sha256 = "1jhmmd7ik1lx9y5niqv5rknhq02pkwmyxc5c0wndp5cyp8hsj0py";
          };
          buildInputs = [ ocamlbuild ];
          buildPhase = "";
          installPhase = ''
            mkdir -p $out/lib/ocaml/4.07.1/site-lib
            make install
          '';
          doCheck = false;
        }) { };
    ocp-ocamlres = self.callPackage
      ({ stdenv, fetchFromGitHub, buildDunePackage, pprint, astring, base }:
        buildDunePackage rec {
          pname = "ocp-ocamlres";
          version = "0.4";

          minimumOCamlVersion = "4.03";
          src = fetchFromGitHub {
            owner = "OCamlPro";
            repo = "${pname}";
            rev = "v${version}";
            sha256 = "0smfwrj8qhzknhzawygxi0vgl2af4vyi652fkma59rzjpvscqrnn";
          };
          buildInputs = [ pprint astring base ];
          buildPhase = "";
          installPhase = ''
            mkdir -p $out/lib/ocaml/4.07.1/site-lib
            mkdir -p $out/lib/ocaml/4.07.1/site-lib//../bin
            make install
          '';
          doCheck = false;
        }) { };

    tezos = self.callPackage ({ stdenv, fetchgit, buildDunePackage, base
      , bigstring, cohttp-lwt, cohttp-lwt-unix, cstruct, ezjsonm, hex, ipaddr
      , js_of_ocaml, cmdliner, easy-format, tls, lwt4, lwt_log
      , mtime, ocplib-endian, ptime, re, rresult, stdio, uri, uutf, zarith
      , libusb1, hidapi, gmp, irmin, alcotest, dum, genspio, ocamlgraph, findlib
      , digestif, ocp-ocamlres, pprint }:
      buildDunePackage rec {
        pname = "tezos";
        version = "0.0.1";

        minimumOCamlVersion = "4.07";

        patches = [ branchInfo.patchFile ];
        src = fetchgit {
          url = "https://gitlab.com/tezos/tezos.git/";
          rev = branchInfo.rev;
          sha256 = branchInfo.sha256;
        };
        preInstall = ''
          cp src/*/*.install .
        '';

        buildInputs = [
          base
          bigstring
          cohttp-lwt
          cohttp-lwt-unix
          cstruct
          ezjsonm
          irmin
          hex
          ipaddr # rmin
          hidapi
          lwt4
          lwt_log
          mtime
          ocplib-endian
          ptime
          re
          rresult
          digestif
          stdio
          uri
          uutf
          zarith
          cmdliner
          # easy-format js_of_ocaml ocp-ocamlres tls
          # alcotest dum pprint
          ocp-ocamlres
          pprint
          ocamlgraph
          findlib
          genspio
        ] ++ [ libusb1 libusb1.out (gmp.override { withStatic = true; }) ];
        doCheck = false;
        buildPhase = ''
          # tezos-node build requires ocp-ocamlres binary in PATH
          PATH=$PATH:${ocp-ocamlres}/lib/ocaml/4.07.1/bin
          dune build src/bin_client/tezos-client.install
          dune build src/bin_node/tezos-node.install
          dune build src/proto_${branchInfo.protoName}/bin_baker/tezos-baker-${branchInfo.binarySuffix}.install
          dune build src/proto_${branchInfo.protoName}/bin_accuser/tezos-accuser-${branchInfo.binarySuffix}.install
          dune build src/proto_${branchInfo.protoName}/bin_endorser/tezos-endorser-${branchInfo.binarySuffix}.install
          dune build src/bin_signer/tezos-signer.install
        '';
        installPhase = ''
          mkdir -p $out/bin
          # tezos-client and tezos-admin
          cp _build/default/src/bin_client/main_client.exe $out/bin/tezos-client
          cp _build/default/src/bin_client/main_admin.exe $out/bin/tezos-client-admin
          # tezos-node
          cp _build/default/src/bin_node/main.exe $out/bin/tezos-node
          # tezos-baker
          cp _build/default/src/proto_${branchInfo.protoName}/bin_baker/main_baker_${branchInfo.protoName}.exe \
          $out/bin/tezos-baker-${branchInfo.binarySuffix}
          # tezos-accuser
          cp _build/default/src/proto_${branchInfo.protoName}/bin_accuser/main_accuser_${branchInfo.protoName}.exe \
          $out/bin/tezos-accuser-${branchInfo.binarySuffix}
          # tezos-endorser
          cp _build/default/src/proto_${branchInfo.protoName}/bin_endorser/main_endorser_${branchInfo.protoName}.exe \
          $out/bin/tezos-endorser-${branchInfo.binarySuffix}
          # tezos-signer
          cp _build/default/src/bin_signer/main_signer.exe $out/bin/tezos-signer
        '';
      }) { };
  });
in oca.tezos
