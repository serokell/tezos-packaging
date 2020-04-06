# SPDX-FileCopyrightText: 2019 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: MPL-2.0
let
  fixOcaml = ocaml:
    (ocaml.overrideAttrs (o: {
      configurePlatforms = [ ];
      dontUpdateAutotoolsGnuConfigScripts = true;
    })).overrideDerivation (o:
      if o.stdenv.hostPlatform != o.stdenv.buildPlatform then {
        preConfigure = ''
          configureFlagsArray+=("CC=$CC" "AS=$AS" "PARTIALLD=$LD -r")
        '';
        configureFlags = o.configureFlags ++ [
          "-host ${o.stdenv.hostPlatform.config} -target ${o.stdenv.targetPlatform.config}"
        ];
      } else
        { });
  fixOcamlBuild = b:
    b.overrideAttrs (o: {
      configurePlatforms = [ ];
      nativeBuildInputs = o.buildInputs;
    });
  dds = x: x.overrideAttrs (o: { dontDisableStatic = true; });
  nixpkgs-fixed = builtins.fetchTarball
    "https://github.com/serokell/nixpkgs/archive/ocaml-cross-fixes-new.tar.gz";
  pkgsNative = import nixpkgs-fixed { };
  pkgs = import nixpkgs-fixed {
    crossSystem = pkgsNative.lib.systems.examples.musl64;
    overlays = [
      (self: super: { ocaml = fixOcaml super.ocaml; })
      (self: super: {
        musl-bin = super.callPackage ./musl-bin.nix { };
        getent = self.musl-bin;
        getconf = self.musl-bin;
        libev = dds super.libev;
        libusb1 = dds (super.libusb1.override { systemd = self.eudev; enableSystemd = true; });
        hidapi = dds (super.hidapi.override { systemd = self.eudev; });
        glib = (super.glib.override { libselinux = null; }).overrideAttrs
          (o: { mesonFlags = o.mesonFlags ++ [ "-Dselinux=disabled" ]; });
        eudev = dds (super.eudev.overrideAttrs
          (o: { nativeBuildInputs = o.nativeBuildInputs ++ [ super.gperf ]; }));
        opaline = fixOcamlBuild (super.opaline.override {
          ocamlPackages = self.ocaml-ng.ocamlPackages_4_09;
        });
        ocaml-ng = super.ocaml-ng // {
          ocamlPackages_4_09 = super.ocaml-ng.ocamlPackages_4_09.overrideScope'
            (oself: osuper: {
              ocaml = fixOcaml osuper.ocaml;
              findlib = fixOcamlBuild osuper.findlib;
              ocamlbuild = fixOcamlBuild osuper.ocamlbuild;
              buildDunePackage = args:
                fixOcamlBuild (osuper.buildDunePackage args);
              result = fixOcamlBuild osuper.result;
              zarith = (osuper.zarith.overrideAttrs (o: {
                configurePlatforms = [ ];
                nativeBuildInputs = o.nativeBuildInputs ++ o.buildInputs;
              })).overrideDerivation (o: {
                preConfigure = ''
                  echo $configureFlags
                '';
                configureFlags = o.configureFlags ++ [
                  "-host ${o.stdenv.hostPlatform.config} -prefixnonocaml ${o.stdenv.hostPlatform.config}-"
                ];
              });
              ocamlgraph = fixOcamlBuild osuper.ocamlgraph;
              easy-format = fixOcamlBuild osuper.easy-format;
              qcheck = fixOcamlBuild osuper.qcheck;
              stringext = fixOcamlBuild osuper.stringext;
              opam-file-format = fixOcamlBuild osuper.opam-file-format;
              dune = fixOcamlBuild osuper.dune;
              digestif = fixOcamlBuild osuper.digestif;
              astring = fixOcamlBuild osuper.astring;
              rresult = fixOcamlBuild osuper.rresult;
              fpath = fixOcamlBuild osuper.fpath;
              ocb-stubblr = fixOcamlBuild osuper.ocb-stubblr;
              cppo = fixOcamlBuild osuper.cppo;
              ocplib-endian = fixOcamlBuild osuper.ocplib-endian;
              ssl = fixOcamlBuild osuper.ssl;
            });
        };
      })
    ];
  };
in import ./default.nix { inherit pkgs; }
