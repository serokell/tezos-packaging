<!--
   - SPDX-FileCopyrightText: 2022 Oxhead Alpha
   - SPDX-License-Identifier: LicenseRef-MIT-OA
   -->
# Release workflow

This document explains the steps and timings of the release process in `tezos-packaging`.

The releasing process is almost fully automated, with the initial release PR being created
at most 4 hours after a new Octez release. The only steps that require manual intervention
are reviews of this initial PR and of the PR that updates macOS brew formulae.
This allows `tezos-packaging` to closely follow Octez releases without large waiting times.

This process can be described by the following diagram:
```mermaid
graph TD;
   classDef CI fill:#d0ffb3,stroke:#000000,color:black
   classDef manually fill:#fbff82,stroke:#000000,color:black
   start(Start)-->check_octez_release{New Octez Release?}:::CI
   style start fill:#ffffff,stroke:#000000,color:black
   CI[Performed by CI]:::CI
   Manually[Performed manually]:::manually
   check_octez_release--No-->wait[Wait 4 hours]:::CI
   wait-->check_octez_release
   check_octez_release--Yes-->tezos_packaging_release_PR[Create release PR in tezos-packaging repo]:::CI
   tezos_packaging_release_PR-->review_release_PR[Review and merge release PR]:::manually
   review_release_PR-->stable_release_check_1{Stable Octez release?}:::CI
   stable_release_check_1--Yes-->github_release[Create new Github release with static binaries]:::CI
   github_release-->publish_stable_native_packages[Publish native packages to the stable Launchpad PPA and Copr Project]:::CI
   github_release-->build_brew_bottles["Build Brew bottles, upload them to the created GitHub {pre-}release"]:::CI
   github_prerelease-->build_brew_bottles
   github_prerelease-->publish_RC_native_packages[Publish native packages to the RC Launchpad PPA and Copr Project]:::CI
   stable_release_check_1--No-->github_prerelease[Create new GitHub pre-release with static binaries]:::CI
   build_brew_bottles-->create_bottles_hashes_PR[Create PR to tezos-packaging repo with formulae bottles' hashes update]:::CI
   create_bottles_hashes_PR-->review_bottles_hashes_PR[Review and merge formulae update PR]:::manually
   review_bottles_hashes_PR-->stable_release_check_2{Stable Octez release?}:::CI
   stable_release_check_2--Yes-->update_stable_mirror[Update stable tezos-packaging mirror repository]:::CI
   stable_release_check_2--No-->update_RC_mirror[Update RC tezos-packaging mirror repository]:::CI
```
