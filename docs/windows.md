<!--
   - SPDX-FileCopyrightText: 2023 Oxhead Alpha
   - SPDX-License-Identifier: LicenseRef-MIT-OA
   -->

# Ubuntu packages on WSL

Octez binaries do not support Windows systems natively, however it's possible to
use Linux binaries with the [Windows Subsystem for Linux](https://learn.microsoft.com/en-us/windows/wsl/).

The simplest option with `tezos-packaging` is to use [Ubuntu on WSL](https://ubuntu.com/wsl)
by following these [step-by-step instructions](https://ubuntu.com/tutorials/install-ubuntu-on-wsl2-on-windows-11-with-gui-support#1-overview).

Once this setup is complete, you can add the launchpad PPA and install packages
in the same way as described in [our documentation for Ubuntu](./ubuntu.md#ubuntu).

Please note: this setup at this point has some limitation, keep reading below for
more info on how to take better advantage of the Ubuntu packages on Windows.

## Ledger devices with WSL

In order to use a [ledger device](https://www.ledger.com/) on WSL some additional preparation steps are needed.

We recommed to use the `usbipd-win` tool and follow [this guide](https://docs.microsoft.com/en-us/windows/wsl/connect-usb)
about connecting usb devices to WSL.

## Systemd units on WSL

Ubuntu packages include services to manage `tezos` software more effectively,
which are necessary for the [baking](./baking.md) and [voting](./voting.md)
wizards.
These services are using `systemd` and you can read more in [the dedicated doc](./systemd.md#ubuntu-and-fedora).

`systemd` is supported on WSL starting from version `0.67.6` and higher.
You can check your version by running the `wsl --version` command.

If that command fails then you need to upgrade your WSL to the Store version.
You can read how to do it [there](https://devblogs.microsoft.com/commandline/a-preview-of-wsl-in-the-microsoft-store-is-now-available/#how-to-install-and-use-wsl-in-the-microsoft-store).
Note that you need to have Windows 11 to install the required version.

After you have installed the required version of WSL along with the distribution
(we recommend using Ubuntu), you need to launch it and configure `systemd`.
The configuration steps are described below.

To enable `systemd` startup on boot you need to follow these steps:

1. Run `sudo nano /etc/wsl.conf`
2. In the `nano` editor add the following lines to the `wsl.conf` file:

```
[boot]
systemd=true
```
3. Close the editor and save your changes using the `ctrl + x` keyboard shortcut.
4. Restart your machine to apply the WSL configuration changes.

To make sure `systemd` is running on your machine use the
`systemctl list-unit-files --type=service` command which should show your
services' status.

You can read more about installing and using `systemd` on WSL in
[this article](https://devblogs.microsoft.com/commandline/systemd-support-is-now-available-in-wsl/).

After you have configured WSL with `systemd`, the [the relative documentation](./systemd.md#ubuntu-and-fedora)
should apply to your system as well.
