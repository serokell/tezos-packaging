# SPDX-FileCopyrightText: 2019 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: MPL-2.0

self: super:
let
  dds = x: x.overrideAttrs (o: { dontDisableStatic = true; });
  release-binaries = import ./release-binaries.nix;
  makeStatic = pkg: libs: flags:
    pkg.overrideAttrs (oa: {
      buildInputs = libs ++ oa.buildInputs;
      OCAMLPARAM = "_,ccopt=-static,cclib=${flags}";
    });
  makeStaticDefaults = pkg:
    makeStatic pkg [ self.libusb1 self.hidapi ]
    "-lusb-1.0 -lhidapi-libusb -ludev";
in {
  ocaml = self.ocaml-ng.ocamlPackages_4_07.ocaml;
  curl = super.curl.override { gssSupport = false; };
  libev = dds super.libev;
  libusb1 = dds (super.libusb1.override {
    systemd = self.eudev;
    enableSystemd = true;
  });
  gdb = null;
  hidapi = dds (super.hidapi.override { systemd = self.eudev; });
  glib = (super.glib.override { libselinux = null; }).overrideAttrs
    (o: { mesonFlags = o.mesonFlags ++ [ "-Dselinux=disabled" ]; });
  eudev = dds (super.eudev.overrideAttrs
    (o: { nativeBuildInputs = o.nativeBuildInputs ++ [ super.gperf ]; }));
  gmp = dds (super.gmp);
  ocamlPackages = super.ocamlPackages.overrideScope' (oself: osuper:
    builtins.listToAttrs (map ({ name, ... }: {
      inherit name;
      value = makeStaticDefaults osuper.${name};
    }) release-binaries));
}
