# SPDX-FileCopyrightText: 2019 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: MPL-2.0
{ pkgs ? import <nixpkgs> { } }:
branchInfo:

let
  oca = pkgs.ocaml-ng.ocamlPackages_4_09.overrideScope' (self: super: {
    sexplib0 = self.callPackage ({ stdenv, fetchFromGitHub, buildDunePackage }:
      buildDunePackage rec {
        pname = "sexplib0";
        version = "0.13.0";

        minimumOCamlVersion = "4.04.2";

        src = fetchFromGitHub {
          owner = "janestreet";
          repo = "${pname}";
          rev = "v${version}";
          sha256 = "1b1bk0xs1hqa12qs5y4h1yl3mq6xml4ya2570dyhdn1j0fbw4g3y";
        };

        buildInputs = [ ];
        doCheck = true;
      }) { };
    parsexp = self.callPackage
      ({ stdenv, fetchFromGitHub, buildDunePackage, sexplib0, base }:
        buildDunePackage rec {
          pname = "parsexp";
          version = "0.13.0";

          minimumOCamlVersion = "4.04.2";

          src = fetchFromGitHub {
            owner = "janestreet";
            repo = "${pname}";
            rev = "v${version}";
            sha256 = "0fsxy5lpsvfadj8m2337j8iprs294dfikqxjcas7si74nskx6l38";
          };

          buildInputs = [ sexplib0 base ];
          doCheck = true;
        }) { };
    sexplib = self.callPackage
      ({ stdenv, fetchFromGitHub, buildDunePackage, sexplib0, base, num, parsexp }:
        buildDunePackage rec {
          pname = "sexplib";
          version = "0.13.0";

          minimumOCamlVersion = "4.04.2";

          src = fetchFromGitHub {
            owner = "janestreet";
            repo = "${pname}";
            rev = "v${version}";
            sha256 = "059ypcyirw00x6dqa33x49930pwxcr3i72qz5pf220js2ai2nzhn";
          };

          buildInputs = [ sexplib0 base num parsexp ];
          doCheck = true;
        }) { };
    base = self.callPackage
      ({ stdenv, fetchFromGitHub, buildDunePackage, sexplib0 }:
        buildDunePackage rec {
          pname = "base";
          version = "0.13.1";

          minimumOCamlVersion = "4.04.2";

          src = fetchFromGitHub {
            owner = "janestreet";
            repo = "${pname}";
            rev = "v${version}";
            sha256 = "08a5aymcgr5svvm8v0v20msd5cad64m6maakfbhz4172g7kd9jzw";
          };

          buildInputs = [ sexplib0 ];
          doCheck = true;
        }) { };
    stdio = self.callPackage
      ({ stdenv, fetchFromGitHub, buildDunePackage, base, sexplib0 }:

        buildDunePackage rec {
          pname = "stdio";
          version = "0.13.0";

          minimumOCamlVersion = "4.04.2";

          src = fetchFromGitHub {
            owner = "janestreet";
            repo = "${pname}";
            rev = "v${version}";
            sha256 = "1hkj9vh8n8p3n5pvx7053xis1pfmqd8p7shjyp1n555xzimfxzgh";
          };

          buildInputs = [ base sexplib0 ];
          doCheck = true;
        }) { };
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
            mkdir -p $out/lib/ocaml/4.09.0/site-lib
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
            mkdir -p $out/lib/ocaml/4.09.0/site-lib
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
            mkdir -p $out/lib/ocaml/4.09.0/site-lib
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
      propagatedBuildInputs = o.propagatedBuildInputs ++ [ self.sexplib self.parsexp ];
    });
    cstruct-sexp = super.cstruct-sexp.overrideDerivation (o: rec {
      propagatedBuildInputs = o.propagatedBuildInputs ++ [ self.parsexp self.sexplib0 self.base ];
    });
    ppx_cstruct = super.ppx_cstruct.overrideDerivation (o: rec {
      propagatedBuildInputs = o.propagatedBuildInputs ++ [ self.parsexp ];
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
      version = "2.5.1";
      name = "cohttp-2.5.1";
      src = pkgs.fetchFromGitHub {
        owner = "mirage";
        repo = "ocaml-${o.pname}";
        rev = "v${version}";
        sha256 = "1rjdsc2d3y65rlqpjq3xqjjr1wxzqqbyjdg5z29vajncvyrpzk1z";
      };
      propagatedBuildInputs = o.propagatedBuildInputs ++ [ self.stdlib-shims ];
    });
    ocaml-compilers-libs = self.callPackage
      ({ stdenv, fetchFromGitHub, buildDunePackage }:
        buildDunePackage rec {
          pname = "ocaml-compilers-libs";
          version = "0.12.1";
          src = pkgs.fetchFromGitHub {
            owner = "janestreet";
            repo = "${pname}";
            rev = "v${version}";
            sha256 = "0jkhwmkrfq3ss5bv6i3m861alcr4ypngs6ci6bmzv3yfl7s8bwdf";
          };
          propagatedBuildInputs = [ ];
        }) { };
    ppx_derivers = self.callPackage
      ({ stdenv, fetchFromGitHub, buildDunePackage, base, sexplib0, stdio }:
        buildDunePackage rec {
          pname = "ppx_derivers";
          version = "1.2.1";
          src = pkgs.fetchFromGitHub {
            owner = "ocaml-ppx";
            repo = "${pname}";
            rev = "${version}";
            sha256 = "0yqvqw58hbx1a61wcpbnl9j30n495k23qmyy2xwczqs63mn2nkpn";
          };
          propagatedBuildInputs = [ base sexplib0 stdio ];
        }) { };
    ppxlib = self.callPackage ({ stdenv, fetchFromGitHub, buildDunePackage, base
      , sexplib0, stdio, ppx_derivers, ocaml-compiler-libs
      , ocaml-migrate-parsetree }:
      buildDunePackage rec {
        pname = "ppxlib";
        minimumOCamlVersion = "4.04";
        version = "0.12.0";
        src = pkgs.fetchFromGitHub {
          owner = "ocaml-ppx";
          repo = "${pname}";
          rev = "${version}";
          sha256 = "1cg0is23c05k1rc94zcdz452p9zn11dpqxm1pnifwx5iygz3w0a1";
        };
        propagatedBuildInputs = [
          base
          sexplib0
          stdio
          ppx_derivers
          ocaml-compiler-libs
          ocaml-migrate-parsetree
        ];
      }) { };
    ppx_sexp_conv = self.callPackage
      ({ stdenv, fetchFromGitHub, buildDunePackage, base, sexplib0, ppxlib }:
        buildDunePackage rec {
          pname = "ppx_sexp_conv";
          minimumOCamlVersion = "4.04";
          version = "0.13.0";
          src = pkgs.fetchFromGitHub {
            owner = "janestreet";
            repo = "${pname}";
            rev = "v${version}";
            sha256 = "0jkhwmkrfq3ss6bv6i3m871alcr4xpngs6ci6bmzv3yfl7s8bwdf";
          };
          propagatedBuildInputs = [ base sexplib0 ppxlib ];
        }) { };
    cohttp-lwt = super.cohttp-lwt.overrideDerivation (o: rec {
      version = "2.5.1";
      name = "cohttp-lwt";
      src = pkgs.fetchFromGitHub {
        owner = "mirage";
        repo = "ocaml-cohttp";
        rev = "v${version}";
        sha256 = "1rjdsc2d3y65rlqpjq3xqjjr1wxzqqbyjdg5z29vajncvyrpzk1z";
      };
      propagatedBuildInputs = o.propagatedBuildInputs
        ++ [ self.stdlib-shims self.sexplib0 self.ppx_sexp_conv ];
    });
    fieldslib = self.callPackage
      ({ stdenv, fetchFromGitHub, buildDunePackage, base, sexplib0 }:
        buildDunePackage rec {
          pname = "fieldslib";
          version = "0.13.0";
          src = pkgs.fetchFromGitHub {
            owner = "janestreet";
            repo = "${pname}";
            rev = "v${version}";
            sha256 = "0nsl0i9vjk73pr70ksxqa65rd5v84jzdaazryfdy6i4a5sfg7bxa";
          };
          propagatedBuildInputs = [ base sexplib0 ];
        }) { };
    ppx_fields_conv = self.callPackage ({ stdenv, fetchFromGitHub
      , buildDunePackage, base, sexplib0, ppxlib, fieldslib }:
      buildDunePackage rec {
        pname = "ppx_fields_conv";
        version = "0.13.0";
        src = pkgs.fetchFromGitHub {
          owner = "janestreet";
          repo = "${pname}";
          rev = "v${version}";
          sha256 = "0biw0fgphj522bj9wgjk263i2w92vnpaabzr5zn0grihp4yqy8w4";
        };
        propagatedBuildInputs = [ base sexplib0 ppxlib fieldslib ];
      }) { };
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
            mkdir -p $out/lib/ocaml/4.09.0/site-lib
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
            mkdir -p $out/lib/ocaml/4.09.0/site-lib
            mkdir -p $out/lib/ocaml/4.09.0/bin
            make install
          '';
          doCheck = false;
        }) { };
    ezjsonm = super.ezjsonm.overrideDerivation (o: rec {
      version = "1.1.0";
      name = "ezjsonm";
      src = pkgs.fetchFromGitHub {
        owner = "mirage";
        repo = "ezjsonm";
        rev = "v${version}";
        sha256 = "064j9pzy01p3dv947khqyn7fkjbs3jmrqsg8limb4abnlaqxxs2s";
      };
      propagatedBuildInputs = o.propagatedBuildInputs ++ [ self.parsexp self.sexplib0 self.base ];
    });
    nocrypto = super.nocrypto.overrideDerivation (o: rec {
      propagatedBuildInputs = o.propagatedBuildInputs ++ [ self.parsexp ];
    });
    fmt = super.fmt.overrideDerivation (o: rec {
      version = "0.8.8";
      name = "fmt";
      src = pkgs.fetchFromGitHub {
        owner = "dbuenzli";
        repo = "fmt";
        rev = "v${version}";
        sha256 = "06700rk442hn2yss04aqv2pr3c0l88zvv6sbwq0hg0fyyacmapl7";
      };
      propagatedBuildInputs = o.propagatedBuildInputs
        ++ [ self.stdlib-shims self.seq ];
    });
    json-data-encoding = self.callPackage ({ buildDunePackage, uri }:
      buildDunePackage rec {
        pname = "json-data-encoding";
        version = "0.8";

        minimumOCamlVersion = "4.03";
        src = builtins.fetchTarball {
          url =
            "https://gitlab.com/nomadic-labs/json-data-encoding/-/archive/v0.8/json-data-encoding-v0.8.tar.gz";
          sha256 = "1c6m2qvi9bm6qjxc38p6cia1f66r0rb9xf6b8svlj3jjymvqw889";
        };
        buildInputs = [ uri ];
        doCheck = false;
      }) { };
    json-data-encoding-bson = self.callPackage
      ({ buildDunePackage, json-data-encoding, ocplib-endian, uri }:
        buildDunePackage rec {
          pname = "json-data-encoding-bson";
          version = "0.8";

          minimumOCamlVersion = "4.03";
          src = builtins.fetchTarball {
            url =
              "https://gitlab.com/nomadic-labs/json-data-encoding/-/archive/v0.8/json-data-encoding-v0.8.tar.gz";
            sha256 = "1c6m2qvi9bm6qjxc38p6cia1f66r0rb9xf6b8svlj3jjymvqw889";
          };
          buildInputs = [ uri ocplib-endian json-data-encoding ];
          doCheck = false;
        }) { };
    lwt-canceler = self.callPackage ({ buildDunePackage, lwt4 }:
      buildDunePackage rec {
        pname = "lwt-canceler";
        version = "0.2";

        minimumOCamlVersion = "4.03";
        src = builtins.fetchTarball {
          url =
            "https://gitlab.com/nomadic-labs/lwt-canceler/-/archive/v0.2/lwt-canceler-v0.2.tar.gz";
          sha256 = "07931486vg83sl1c268i0vyw61l8n8xs2krjsj43070zljqi8rf1";
        };
        buildInputs = [ lwt4 ];
        doCheck = false;
      }) { };
    lwt-watcher = self.callPackage ({ buildDunePackage, lwt4 }:
      buildDunePackage rec {
        pname = "lwt-watcher";
        version = "0.1";

        minimumOCamlVersion = "4.03";
        src = builtins.fetchTarball {
          url =
            "https://gitlab.com/nomadic-labs/lwt-watcher/-/archive/v0.1/lwt-watcher-v0.1.tar.gz";
          sha256 = "0kaf7py02i0dn9rvrbzxh4ljfg059wc8xvm093m9wy7lsa68rax9";
        };
        buildInputs = [ lwt4 ];
        doCheck = false;
      }) { };

    data-encoding = self.callPackage ({ buildDunePackage, json-data-encoding
      , json-data-encoding-bson, ezjsonm, zarith, uri, ocplib-endian }:
      buildDunePackage rec {
        pname = "data-encoding";
        version = "0.2";

        minimumOCamlVersion = "4.03";
        src = builtins.fetchTarball {
          url =
            "https://gitlab.com/nomadic-labs/data-encoding/-/archive/0.2/data-encoding-0.2.tar.gz";
          sha256 = "0d9c2ix2imqk4r0jfhnwak9laarlbsq9kmswvbnjzdm2g0hwin1d";
        };
        buildInputs = [
          json-data-encoding
          json-data-encoding-bson
          ezjsonm
          zarith
          uri
          ocplib-endian
        ];
        doCheck = false;
      }) { };

    resto = self.callPackage ({ buildDunePackage, json-data-encoding
      , json-data-encoding-bson, uri, ocplib-endian, lwt4 }:
      buildDunePackage rec {
        pname = "resto";
        version = "0.4";

        minimumOCamlVersion = "4.03";
        src = builtins.fetchTarball {
          url =
            "https://gitlab.com/nomadic-labs/resto/-/archive/v0.4/resto-v0.4.tar.gz";
          sha256 = "0v0cyf8na21fnvy3abhhnnw8msh16dqcrp61pzaxj839rm62h3vy";
        };
        buildInputs =
          [ json-data-encoding json-data-encoding-bson uri ocplib-endian lwt4 ];
        doCheck = false;
      }) { };

    resto-json = self.callPackage ({ buildDunePackage, json-data-encoding
      , json-data-encoding-bson, uri, ocplib-endian, lwt4, resto }:
      buildDunePackage rec {
        pname = "resto-json";
        version = "0.4";

        minimumOCamlVersion = "4.03";
        src = builtins.fetchTarball {
          url =
            "https://gitlab.com/nomadic-labs/resto/-/archive/v0.4/resto-v0.4.tar.gz";
          sha256 = "0v0cyf8na21fnvy3abhhnnw8msh16dqcrp61pzaxj839rm62h3vy";
        };
        buildInputs = [
          json-data-encoding
          json-data-encoding-bson
          uri
          ocplib-endian
          lwt4
          resto
        ];
        doCheck = false;
      }) { };

    resto-directory = self.callPackage ({ buildDunePackage, json-data-encoding
      , json-data-encoding-bson, uri, ocplib-endian, lwt4, resto, resto-json }:
      buildDunePackage rec {
        pname = "resto-directory";
        version = "0.4";

        minimumOCamlVersion = "4.03";
        src = builtins.fetchTarball {
          url =
            "https://gitlab.com/nomadic-labs/resto/-/archive/v0.4/resto-v0.4.tar.gz";
          sha256 = "0v0cyf8na21fnvy3abhhnnw8msh16dqcrp61pzaxj839rm62h3vy";
        };
        buildInputs = [
          json-data-encoding
          json-data-encoding-bson
          uri
          ocplib-endian
          lwt4
          resto
          resto-json
        ];
        doCheck = false;
      }) { };

    resto-cohttp = self.callPackage ({ buildDunePackage, json-data-encoding
      , json-data-encoding-bson, uri, ocplib-endian, lwt4, resto, resto-json
      , resto-directory, cohttp-lwt }:
      buildDunePackage rec {
        pname = "resto-cohttp";
        version = "0.4";

        minimumOCamlVersion = "4.03";
        src = builtins.fetchTarball {
          url =
            "https://gitlab.com/nomadic-labs/resto/-/archive/v0.4/resto-v0.4.tar.gz";
          sha256 = "0v0cyf8na21fnvy3abhhnnw8msh16dqcrp61pzaxj839rm62h3vy";
        };
        buildInputs = [
          json-data-encoding
          json-data-encoding-bson
          uri
          ocplib-endian
          lwt4
          resto
          resto-json
          resto-directory
          cohttp-lwt
        ];
        doCheck = false;
      }) { };

    resto-cohttp-client = self.callPackage ({ buildDunePackage
      , json-data-encoding, json-data-encoding-bson, uri, ocplib-endian, lwt4
      , resto, resto-json, resto-directory, cohttp-lwt, resto-cohttp }:
      buildDunePackage rec {
        pname = "resto-cohttp-client";
        version = "0.4";

        minimumOCamlVersion = "4.03";
        src = builtins.fetchTarball {
          url =
            "https://gitlab.com/nomadic-labs/resto/-/archive/v0.4/resto-v0.4.tar.gz";
          sha256 = "0v0cyf8na21fnvy3abhhnnw8msh16dqcrp61pzaxj839rm62h3vy";
        };
        buildInputs = [
          json-data-encoding
          json-data-encoding-bson
          uri
          ocplib-endian
          lwt4
          resto
          resto-json
          resto-directory
          cohttp-lwt
          resto-cohttp
        ];
        doCheck = false;
      }) { };

    resto-cohttp-server = self.callPackage ({ buildDunePackage
      , json-data-encoding, json-data-encoding-bson, uri, ocplib-endian, lwt4
      , resto, resto-json, resto-directory, cohttp-lwt, resto-cohttp
      , cohttp-lwt-unix }:
      buildDunePackage rec {
        pname = "resto-cohttp-server";
        version = "0.4";

        minimumOCamlVersion = "4.03";
        src = builtins.fetchTarball {
          url =
            "https://gitlab.com/nomadic-labs/resto/-/archive/v0.4/resto-v0.4.tar.gz";
          sha256 = "0v0cyf8na21fnvy3abhhnnw8msh16dqcrp61pzaxj839rm62h3vy";
        };
        buildInputs = [
          json-data-encoding
          json-data-encoding-bson
          uri
          ocplib-endian
          lwt4
          resto
          resto-json
          resto-directory
          cohttp-lwt
          resto-cohttp
          cohttp-lwt-unix
        ];
        doCheck = false;
      }) { };

    tezos = self.callPackage ({ stdenv, fetchgit, buildDunePackage, base
      , bigstring, cohttp-lwt, cohttp-lwt-unix, cstruct, ezjsonm, hex, ipaddr
      , js_of_ocaml, cmdliner, easy-format, tls, lwt4, lwt_log, mtime
      , ocplib-endian, ptime, re, rresult, stdio, uri, uutf, zarith, libusb1
      , hidapi, gmp, irmin, alcotest, dum, genspio, ocamlgraph, findlib
      , digestif, ocp-ocamlres, pprint, upx, json-data-encoding
      , json-data-encoding-bson, lwt-canceler, lwt-watcher, data-encoding, resto
      , resto-directory, resto-cohttp, resto-cohttp-client, resto-cohttp-server
      }:
      buildDunePackage rec {
        pname = "tezos";
        version = "0.0.1";

        minimumOCamlVersion = "4.07";

        patches = branchInfo.patches;
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
          easy-format
          dum
          # js_of_ocaml ocp-ocamlres tls
          # alcotest pprint
          ocp-ocamlres
          pprint
          ocamlgraph
          findlib
          genspio
          json-data-encoding
          json-data-encoding-bson
          lwt-canceler
          lwt-watcher
          data-encoding
          resto
          resto-directory
          resto-cohttp
          resto-cohttp-client
          resto-cohttp-server
        ] ++ [ libusb1 libusb1.out (gmp.override { withStatic = true; }) upx ];
        doCheck = false;
        protocolsNames = map (x: x.protocolName) branchInfo.protocols;
        buildPhase = ''
          # tezos-node build requires ocp-ocamlres binary in PATH
          PATH=$PATH:${ocp-ocamlres}/lib/ocaml/4.09.0/bin
          install_files=()
          for protocol_name in $protocolsNames; do
            protocol_suffix=$(echo "$protocol_name" | tr "_" "-")
            install_files+=("src/proto_$protocol_name}/bin_baker/tezos-baker-$protocol_suffix.install" \
                            "src/proto_$protocol_name}/bin_accuser/tezos-accuser-$protocol_suffix.install" \
                            "src/proto_$protocol_name}/bin_endorser/tezos-endorser-$protocol_suffix.install")
          done
          dune build src/bin_client/tezos-client.install src/bin_node/tezos-node.install \
          src/bin_signer/tezos-signer.install src/lib_protocol_compiler/tezos-protocol-compiler.install "$(install_files[@])"

        '';
        installPhase = ''
          mkdir -p $out/bin
          # tezos-client and tezos-admin
          cp _build/default/src/bin_client/main_client.exe $out/bin/tezos-client
          cp _build/default/src/bin_client/main_admin.exe $out/bin/tezos-admin-client
          # tezos-node
          cp _build/default/src/bin_node/main.exe $out/bin/tezos-node
          # tezos-signer
          cp _build/default/src/bin_signer/main_signer.exe $out/bin/tezos-signer
          # tezos-protocol-compiler
          cp _build/default/src/lib_protocol_compiler/main_native.exe $out/bin/tezos-protocol-compiler
          # Reuse license from tezos repo in packaging
          for protocol_name in $protocolsNames; do
            protocol_suffix=$(echo "$protocol_name" | tr "_" "-")
            # tezos-baker
            cp _build/default/src/proto_"$protocol_name"/bin_baker/main_baker_"$protocol_name".exe \
              $out/bin/tezos-baker-"$protocol_suffix"
            # tezos-accuser
            cp _build/default/src/proto_"$protocol_name"/bin_accuser/main_accuser_"$protocol_name".exe \
              $out/bin/tezos-accuser-"$protocol_suffix"
            # tezos-endorser
            cp _build/default/src/proto_"$protocol_name"/bin_endorser/main_endorser_"$protocol_name".exe \
              $out/bin/tezos-endorser-"$protocol_suffix"
          done
          cp LICENSE $out/LICENSE
          # Compress binaries with upx
          upx $out/bin/*
        '';
      }) { };
  });
in oca.tezos
