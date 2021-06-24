## Description

This PR introduces a new <!-- insert new version here --> release in tezos-packaging.

<!-- Depending on the type of the release some of the points below can be ommited.

E.g. in case we introduce a new changes to our native packages, it's not necessary to bump
used Tezos sources, create a new release in this repository and update brew formulas.

Note that opam-repository is usually updated with some delay, so CI may fail
due to lack of updated opam Tezos packages. In such case feel free to comment
out native-packaging-related CI steps from the pipeline until the opam-repository
is updated.
-->

<!-- List issues which are going to be resolved in the new packages from this
release. Write 'None' if there are no related issues.

For example:
Follows #202, #210
-->

Follows #

### Changes related to the creation of a release (conditional)

- [ ] I updated Tezos sources and opam-repository (if needed) revisions in [sources.json](../../tree/master/nix/nix/sources.json).
- [ ] I removed old bottles hashes from the brew formulas in [Formula directory](../../tree/master/Formula).
- [ ] I updated `url :tag` and `version`s in brew formulas..
- [ ] I updated release number in [meta.json](../../tree/master/meta.json).

#### In case the new Tezos release provides a new protocol and corresponding testnet

- [ ] I supported new protocol in [protocols.json](../../tree/master/protocols.json).
- [ ] I supported new protocol and testnet in native packaging.
- [ ] I supported new protocol and testnet in brew formulas.
- [ ] I added tests for the new protocol and testnet.

### Things to do after this release PR is merged

<!--
Some of the changes are done after the new release is created, consider following
and checking unfinished points in the merged release PR using this template.
-->

#### Create a new release in this repository

- [ ] I created a new release that is based on the latest autorelease created by the CI.

#### Update brew bottles and repository mirrors

- [ ] I compiled brew bottles using [`build-bottles.sh`](../../tree/scripts/build-bottles.sh) script and uploaded them to the created release.
- [ ] I added new bottles sha256 hashes to the brew formulas.
- [ ] I pushed changes to either [tezos-packaging-rc](https://github.com/serokell/tezos-packaging-rc) or
      [tezos-packaging-stable](https://github.com/serokell/tezos-packaging-stable) mirror repositories.

#### Publish new native packages

Once [opam-repository](https://opam.ocaml.org/packages/) is updated with the new version of Tezos packages.

- [ ] I published new Ubuntu packages, see [these instructions](../../tree/master/docker#source-packages-and-publishing-them-on-launchpad-ppa).
- [ ] I published new Fedora packages, see [these instructions](../../tree/master/docker#srcrpm-packages).

#### Update documentation

- [ ] I updated [README.md](../../tree/master/README.md).
- [ ] I updated [baking doc](../../tree/master/docs/baking.md).
