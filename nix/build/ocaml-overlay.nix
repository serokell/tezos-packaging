# SPDX-FileCopyrightText: 2021-2022 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

{ sources, protocols, opam-nix, craneLib, rust-toolchain, ... }:

self: super:
let
  pkgs = super;
in
with opam-nix.lib.${self.system}; let
  zcash-overlay = import ./zcash-overlay.nix;
  hacks = import ./hacks.nix;
  octezScope = buildOpamProject' {
    repos = with sources; [opam-repository];
    recursive = true;
    resolveArgs = {};
  } sources.tezos {};
in {
  octezPackages = (octezScope.overrideScope' (pkgs.lib.composeManyExtensions [
      (_: # Nullify all the ignored protocols so that we don't build them
        builtins.mapAttrs (name: pkg:
          if builtins.any
          (proto: !isNull (builtins.match ".*${proto}.*" name))
          protocols.ignored then
            null
          else
            pkg))
      hacks
      zcash-overlay
      (final: prev:
        let
          vendored-deps = dir:
          let
            src = sources.tezos;
            commonArgs = {
              inherit src;
              buildInputs = [ pkgs.ocaml ];
              cargoToml = "${src}/src/${dir}/Cargo.toml";
              cargoLock = "${src}/src/${dir}/Cargo.lock";
              postUnpack = ''
                cd $sourceRoot/src/${dir}
                sourceRoot="."
              '';
              strictDeps = true;
              OCAMLOPT = "${pkgs.ocaml}/bin/ocamlopt";
              OCAML_WHERE_PATH = "ocaml";
              OCTEZ_RUST_DEPS_NO_WASMER_HEADERS = true;
            };
          in craneLib.vendorCargoDeps commonArgs;

          injectRustDeps = dir: drv:
            let deps = vendored-deps dir;
            in {
            buildInputs = drv.buildInputs ++ [
              deps
              rust-toolchain
            ];
            configurePhase = ''
              export PATH="${rust-toolchain}/bin:$PATH"
              cat ${deps}/config.toml >> ./src/${dir}/.cargo/config.toml
            '' + drv.configurePhase;
          };
        in {
        octez-rust-deps = prev.octez-rust-deps.overrideAttrs (injectRustDeps "rust_deps");
        octez-rustzcash-deps = prev.octez-rustzcash-deps.overrideAttrs (injectRustDeps "rustzcash_deps");
        octez-l2-libs = (prev.octez-l2-libs.overrideAttrs (injectRustDeps "rust_deps")).overrideAttrs (injectRustDeps "rustzcash_deps");
      })
    ]));
}
