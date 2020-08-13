# Contribution Guidelines

## Reporting Issues

Please [open an issue](https://github.com/serokell/tezos-packaging/issues/new/choose)
if you find a bug or have a feature request.
Before submitting a bug report or feature request, check to make sure it hasn't already been submitted

The more detailed your report is, the faster it can be resolved.
If you report a bug, please provide steps to reproduce this bug and revision of code in which this bug reproduces.


## Code

If you would like to contribute code to fix a bug, add a new feature, or
otherwise improve our project, pull requests are most welcome.

## Quick maintenance guide

- Tezos revision is located in the [`sources.json`](../nix/nix/sources.json) file.
  You can either update it manually to newer revision or use `niv` tool.
  In order to do that run
  `niv update tezos -a ref=<tag from tezos repo> -a rev=<commit in this tag>`
  from the [`nix/`](../nix) directory. This command will update sources to some commit
  from the given tag.
- Used tezos protocols can be changed by [`proto`](../script/proto) script.
  This script requires `jq` and `moreutils` to be installed.
  Currently used protocols are displayed in [`protocols.json`](../protocols.json).
  - To add a new protocol, `./proto activate ...`.
  - To stop building protocol-specific binaries for a protocol, but keep supporting it in
    multi-protocol binaries, `./proto allow`.
  - To deprecate a protocol, `./proto ignore ...`.

### Nix specific maintenance

All nix related files are located in the [nix](./nix) directory.

If the build breaks because of a dependency issue, `nix repl pkgs.nix`
can be very useful to investigate it.

## Legal

We want to make sure that our projects come with correct licensing information
and that this information is machine-readable, thus we are following the
[REUSE Practices][reuse] – feel free to click the link and read about them,
but, basically, it all boils down to the following:

  * Add the following header at the very top (but below the shebang, if there
    is one) of each source file in the repository (yes, each and every source
    file – it is not as hard as it might sound):

    ```
    # SPDX-FileCopyrightText: 2019 TQ Tezos <https://tqtezos.com/>
    #
    # SPDX-License-Identifier: MPL-2.0
    ```

    (This is an example for Nix; adapt it as needed for other languages.)

    The license identifier should be the same as the one in the `LICENSE` file.

  * If you are copying any source files from some other project, and they do not
    contain a header with a copyright and a machine-readable license identifier,
    add it, but be extra careful and make sure that information you are recording
    is correct.

    If the license of the file is different from the one used in the project and
    you do not plan to relicense it, use the appropriate license identifier and
    make sure the license text exists in the `LICENSES` directory.

    If the file contains the entire license in its header, it is best to move the
    text to a separate file in the `LICENSES` directory and leave a reference.

  * If you are copying pieces of code from some other project, leave a note in the
    comments, stating where you copied it from, who is the copyright owner, and
    what license applies.

  * All the same rules apply to documentation that is stored in the repository.

These simple rules should cover most of situation you are likely to encounter.
In case of doubt, consult the [REUSE Practices][reuse] document.

[reuse]: https://reuse.software/spec/
