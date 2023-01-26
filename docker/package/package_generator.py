# SPDX-FileCopyrightText: 2021 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

import os
import sys
import shutil
import argparse
from .fedora import build_fedora_package
from .ubuntu import build_ubuntu_package
from .packages import packages as all_packages

# fixed output dir in container
output_dir = "out"

parser = argparse.ArgumentParser()
parser.add_argument("--os", required=True, choices=["ubuntu", "fedora"])
parser.add_argument(
    "-t", "--type", help="package type", required=True, choices=["source", "binary"]
)
parser.add_argument(
    "-p",
    "--packages",
    help="specify binaries to package",
    nargs="+",
)
parser.add_argument(
    "-d",
    "--distributions",
    help="specify distributions to package for",
    nargs="+",
)
parser.add_argument(
    "--binaries-dir",
    help="provide a directory with exiting prebuilt binaries",
    type=os.path.abspath,
)
parser.add_argument(
    "--sources-dir",
    help="specify directory with source archive(s) for ubuntu packages",
    type=os.path.abspath,
)


def get_ubuntu_run_deps(binaries_dir):
    """
    List all the ubuntu run dependencies. Return an empty list when using prebuilt static binaries.
    """
    if binaries_dir:
        return []

    return [
        "libev-dev",
        "libgmp-dev",
        "libhidapi-dev",
        "libffi-dev",
        "zlib1g-dev",
        "libpq-dev",
    ]


def get_fedora_run_deps(binaries_dir):
    """
    List all the fedora run dependencies. Return an empty list when using prebuilt static binaries.
    """
    if binaries_dir:
        return []

    return [
        "libev-devel",
        "gmp-devel",
        "hidapi-devel",
        "libffi-devel",
        "zlib-devel",
        "libpq-devel",
    ]


def get_build_deps(binaries_dir):
    """
    List all the common build dependencies. Return an empty list when using prebuilt static binaries.
    """
    if binaries_dir:
        return ["make", "wget"]

    return [
        "make",
        "cmake",
        "m4",
        "perl",
        "pkg-config",
        "wget",
        "unzip",
        "rsync",
        "gcc",
        "cargo",
        "opam",
        "git",
        "autoconf",
        "coreutils",
    ]


def main():

    args = parser.parse_args()

    target_os = args.os

    is_source = args.type == "source"

    source_archives = os.listdir(args.sources_dir) if args.sources_dir else []

    binaries_dir = args.binaries_dir

    if target_os == "ubuntu":
        run_deps = get_ubuntu_run_deps(binaries_dir)
    elif target_os == "fedora":
        run_deps = get_fedora_run_deps(binaries_dir)

    build_deps = get_build_deps(binaries_dir)

    common_deps = run_deps + build_deps

    home = os.environ["HOME"]

    os.makedirs(output_dir, exist_ok=True)

    distributions = list(args.distributions)

    packages = []

    for package_name in args.packages:
        packages.append(all_packages[package_name])

    if is_source and source_archives:
        errors = []
        for package in packages:
            if getattr(package, "letter_version", None) is None:
                source_archive = (
                    f"{package.name.lower()}_{package.meta.version}.orig.tar.gz"
                )
                if source_archive in source_archives:
                    package.source_archive = os.path.join(
                        args.sources_dir, source_archive
                    )
                else:
                    errors.append(
                        f"ERROR: supplied source dir does not contain source archive for {package.name}"
                    )
        if errors:
            print("\n" + "\n".join(errors) + "\n")
            sys.exit(1)

    if target_os == "ubuntu":
        for package in packages:
            build_ubuntu_package(
                package,
                distributions,
                common_deps,
                is_source,
                getattr(package, "source_archive", None),
                binaries_dir,
            )

        if not is_source:
            exts = [".deb"]
        else:
            exts = [".orig.tar.gz", ".dsc", ".changes", ".debian.tar.xz", ".buildinfo"]

        artifacts_dir = "."

    elif target_os == "fedora":
        for package in packages:
            build_fedora_package(
                package,
                build_deps,
                run_deps,
                is_source,
                distributions,
                binaries_dir,
            )

        exts = [".src.rpm"] if is_source else [".rpm"]

        subdir = "SRPMS" if is_source else "RPMS/x86_64"
        artifacts_dir = f"{home}/rpmbuild/{subdir}"

    for f in os.listdir(artifacts_dir):
        for ext in exts:
            if f.endswith(ext):
                shutil.copy(f"{artifacts_dir}/{f}", os.path.join(output_dir, f))


if __name__ == "__main__":
    main()
