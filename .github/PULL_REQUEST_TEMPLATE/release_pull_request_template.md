## Description

This PR introduces a new <!-- insert new version here --> release in tezos-packaging.

<!-- Depending on the type of the release some of the points below can be omitted.

E.g. in case we introduce a new changes to our native packages, it's not necessary to bump
used Tezos sources, create a new release in this repository and update brew formulas.
-->

<!-- List issues which are going to be resolved in the new packages from this
release. Write 'None' if there are no related issues.

For example:
Follows #202, #210
-->

Follows #

### Changes related to the creation of a release (conditional)

- [ ] I updated Tezos sources and opam-repository (if needed) revisions in [sources.json](/serokell/tezos-packaging/tree/master/nix/nix/sources.json).
    The opam-repository revision should be the same as the one defined in
    [`tezos/tezos`](https://gitlab.com/tezos/tezos/-/blob/master/scripts/version.sh) for the relevant tag.
- [ ] I removed old bottles hashes from the brew formulas in [Formula directory](/serokell/tezos-packaging/tree/master/Formula).
- [ ] I updated `url :tag` and `version`s in brew formulas.
- [ ] I updated release number in [meta.json](/serokell/tezos-packaging/tree/master/meta.json).
- [ ] If the native release version was updated, I reset the `letter_version` in [model.py](/serokell/tezos-packaging/tree/master/docker/package/model.py).

#### In case the new Tezos release provides a new protocol and corresponding testnet

- [ ] I supported new protocol in [protocols.json](/serokell/tezos-packaging/tree/master/protocols.json).
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

- [ ] I compiled brew bottles for all required macOS versions using [`build-bottles.sh`](/serokell/tezos-packaging/tree/scripts/build-bottles.sh)
      script and uploaded them to the created release.
      Note that for this you'll need a macOS machine running each required version.
- [ ] I added new bottles sha256 hashes to the brew formulas.
- [ ] I pushed changes to either [tezos-packaging-rc](https://github.com/serokell/tezos-packaging-rc) or
      [tezos-packaging-stable](https://github.com/serokell/tezos-packaging-stable) mirror repositories.

#### Publish new native packages

- [ ] I published new Ubuntu packages, see [these instructions](/serokell/tezos-packaging/tree/master/docker#source-packages-and-publishing-them-on-launchpad-ppa).
- [ ] I published new Fedora packages, see [these instructions](/serokell/tezos-packaging/tree/master/docker#srcrpm-packages).

#### Update documentation

- [ ] I updated [README.md](/serokell/tezos-packaging/tree/master/README.md).
- [ ] I updated [baking doc](/serokell/tezos-packaging/tree/master/docs/baking.md).
