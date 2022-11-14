# SPDX-FileCopyrightText: 2022 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

{ pkgs, ...}:
with pkgs;
mkShell {
  buildInputs = [
    python3
  ];
}
