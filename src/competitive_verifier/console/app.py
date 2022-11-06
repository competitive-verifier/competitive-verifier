import argparse
import os
import pathlib
import sys
from logging import DEBUG, INFO, getLogger
from typing import Optional

import pkg_resources

import competitive_verifier.config

_config_directory_name = competitive_verifier.config.config_dir.name


def find_project_root_directory() -> Optional[pathlib.Path]:
    dir = pathlib.Path.cwd()
    if (dir / _config_directory_name).exists():
        return dir
    for dir in dir.parents:
        if (dir / _config_directory_name).exists():
            return dir
    return None


# Move to directory which contains .competitive-verifier/
orig_directory = pathlib.Path.cwd()
root = find_project_root_directory()
if root is None:
    root = orig_directory
else:
    os.chdir(root)


logger = getLogger(__name__)


def get_parser() -> argparse.ArgumentParser:
    import competitive_verifier.documents.main as docs
    import competitive_verifier.download.main as download
    import competitive_verifier.verify.main as verify

    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument(
        "--version",
        action="store_true",
        help="print the online-judge-tools version number",
    )

    subparsers = parser.add_subparsers(dest="subcommand")

    subparser = subparsers.add_parser("verify")
    verify.argument_verify(subparser)

    subparser = subparsers.add_parser("docs")
    docs.argument_docs(subparser)

    subparser = subparsers.add_parser("download")
    download.argument_download(subparser)

    return parser


def main(args: Optional[list[str]] = None):
    import competitive_verifier.documents.main as docs
    import competitive_verifier.download.main as download
    import competitive_verifier.verify.main as verify
    from competitive_verifier.log import configure_logging

    parser = get_parser()
    parsed = parser.parse_args(args)

    if parsed.version:
        print(pkg_resources.get_distribution("competitive-verifier"))
        sys.exit(0)

    default_level = INFO
    if parsed.verbose:
        default_level = DEBUG
    configure_logging(default_level=default_level)

    logger.info("Project root: %s", str(pathlib.Path.cwd().resolve(strict=True)))

    os.chdir(orig_directory)
    args_dict = vars(parsed)
    for k, v in args_dict.items():
        if isinstance(v, pathlib.Path):
            args_dict[k] = v.resolve(strict=True)
    os.chdir(root)

    if parsed.subcommand == "download":
        if not download.run(parsed):
            sys.exit(1)
    elif parsed.subcommand == "verify":
        verifier = verify.run(parsed)
        if not verifier.force_result.is_success():
            sys.exit(1)
    elif parsed.subcommand == "docs":
        if not docs.run(parsed):
            sys.exit(1)


if __name__ == "__main__":
    main()
