# SPDX-FileCopyrightText: 2021 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ
{ git_diff }:
let
  pkgs = (import ../. {}).pkgs;
  pipeline = import ./pipeline.nix;
  inherit (pkgs) lib;
  inherit (lib) any crossLists filter splitString;

  splitted_diff = (splitString "\n" git_diff);

  filter_steps = { steps, diff }: filter (step:
      if ! step ? only_changes
      then true
      else
        let
          only_changes = step.only_changes;
          bool_list = crossLists
            (diff_element: regex: builtins.match regex diff_element != null)
            [ diff only_changes ];
        in any (x: x) bool_list
    ) steps;

  remove_only_changes_attr =
    step: if builtins.isString step then step else builtins.removeAttrs step ["only_changes"];

  filter_pipeline = { pipeline, diff }:
    pipeline // { steps = map remove_only_changes_attr (filter_steps { inherit (pipeline) steps; inherit diff; }); };

in pkgs.writeText "pipeline.yml"
  (builtins.toJSON (filter_pipeline
    { pipeline = pipeline; diff = splitted_diff; }
  ))
