# SPDX-FileCopyrightText: 2021 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

import os
import sys
import shutil
import argparse
import urllib.request
from .fedora import build_fedora_package
from .ubuntu import build_ubuntu_package
from .packages import packages as all_packages
from .model import TezosBinaryPackage

# fixed output dir in container
output_dir = "out"

common_parser = argparse.ArgumentParser()
common_parser.add_argument("--os", choices=["ubuntu", "fedora"])
common_parser.add_argument(
    "-t", "--type", help="package type", required=True, choices=["source", "binary"]
)
common_parser.add_argument(
    "-p",
    "--packages",
    help="specify binaries to package",
    nargs="+",
)
common_parser.add_argument(
    "-d",
    "--distributions",
    help="specify distributions to package for",
    nargs="+",
)
common_parser.add_argument(
    "--binaries-dir",
    help="provide a directory with exiting prebuilt binaries",
    type=os.path.abspath,
)


def make_ubuntu_parser(parser):
    parser.add_argument(
        "--sources-dir",
        help="specify directory with source archive(s) for ubuntu packages",
        type=os.path.abspath,
    )
    parser.add_argument(
        "--launchpad-sources",
        help="download sources from launchpad instead of providing them",
        action="store_true",
    )
    parser.set_defaults(launchpad_sources=False)

    return parser


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


def build_fedora(args):

    target_os = args.os

    is_source = args.type == "source"

    binaries_dir = args.binaries_dir

    build_deps = get_build_deps(binaries_dir)

    home = os.environ["HOME"]

    os.makedirs(output_dir, exist_ok=True)

    distributions = list(args.distributions)

    packages = []

    for package_name in args.packages:
        packages.append(all_packages[package_name])

    for package in packages:
        run_deps = (
            get_fedora_run_deps(binaries_dir)
            if isinstance(package, TezosBinaryPackage)
            else []
        )
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

    with open(os.path.join(output_dir, ".artifact_list"), "w") as artifact_list:
        for f in os.listdir(artifacts_dir):
            for ext in exts:
                if f.endswith(ext):
                    artifact_list.write(f"{f}\n")
                    shutil.copy(f"{artifacts_dir}/{f}", os.path.join(output_dir, f))


def build_ubuntu(args):

    target_os = args.os

    is_source = args.type == "source"

    source_archives = os.listdir(args.sources_dir) if args.sources_dir else []

    dl_sources = args.launchpad_sources

    binaries_dir = args.binaries_dir

    build_deps = get_build_deps(binaries_dir)

    home = os.environ["HOME"]

    os.makedirs(output_dir, exist_ok=True)

    distributions = list(args.distributions)

    packages = []

    for package_name in args.packages:
        packages.append(all_packages[package_name])

    if is_source:
        errors = []
        if source_archives:
            for package in packages:
                source_archive = (
                    f"{package.name.lower()}_{package.meta.version}.orig.tar.gz"
                )
                if source_archive in source_archives:
                    package.source_archive = os.path.join(
                        args.sources_dir, source_archive
                    )
                elif getattr(package, "letter_version", None) is None:
                    # We throw an error if the source is missing, unless the package is
                    # tezos-baking, for which we don't need new sources.
                    errors.append(
                        f"ERROR: supplied source dir does not contain source archive for {package.name}"
                    )
        elif dl_sources:
            for package in packages:
                if getattr(package, "letter_version", None) is None:
                    version = package.meta.version
                    repo = (
                        "tezos-rc" if "rc" in version or "beta" in version else "tezos"
                    )
                    name = package.name.lower()
                    # distributions list is always unempty at this point
                    # and sources archive is the same for all distributions
                    dist = distributions[0]
                    url = f"https://launchpad.net/~serokell/+archive/ubuntu/{repo}/+sourcefiles/{name}/2:{version}-0ubuntu1~{dist}/{name}_{version}.orig.tar.gz"
                    source_archive = f"{name}_{package.meta.version}.orig.tar.gz"
                    try:
                        urllib.request.urlretrieve(
                            url,
                            source_archive,
                            lambda count, block_size, total_size: print(
                                f"{package.name} source is downloading: "
                                + str(round(count * block_size / total_size * 100, 2))
                                + "%",
                                end="\r",
                            ),
                        )
                        print(f"{package.name} source was downloaded successfully")
                        package.source_archive = os.path.realpath(source_archive)
                    except (urllib.error.URLError, ValueError):
                        errors.append(
                            f"ERROR: source archive for {package.name} is not available"
                        )
        if errors:
            print("\n" + "\n".join(errors) + "\n")
            sys.exit(1)

    for package in packages:
        run_deps = (
            get_ubuntu_run_deps(binaries_dir)
            if isinstance(package, TezosBinaryPackage)
            else []
        )
        common_deps = build_deps + run_deps
        build_ubuntu_package(
            package,
            distributions,
            common_deps,
            run_deps,
            is_source,
            getattr(package, "source_archive", None),
            binaries_dir,
        )

    if not is_source:
        exts = [".deb"]
    else:
        exts = [".orig.tar.gz", ".dsc", ".changes", ".debian.tar.xz", ".buildinfo"]

    artifacts_dir = "."

    with open(os.path.join(output_dir, ".artifact_list"), "w") as artifact_list:
        for f in os.listdir(artifacts_dir):
            for ext in exts:
                if f.endswith(ext):
                    artifact_list.write(f"{f}\n")
                    shutil.copy(f"{artifacts_dir}/{f}", os.path.join(output_dir, f))


def main():

    args, _ = common_parser.parse_known_args()

    if args.os == "ubuntu":
        args = make_ubuntu_parser(common_parser).parse_args()
        build_ubuntu(args)
    elif args.os == "fedora":
        args = common_parser.parse_args()
        build_fedora(args)


if __name__ == "__main__":
    main()
