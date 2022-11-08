import argparse
import importlib.metadata
import os
import pathlib
import sys
from logging import DEBUG, INFO, getLogger
from typing import Optional

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
    import competitive_verifier.merge_result.main as merge_result
    import competitive_verifier.verify.main as verify

    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument(
        "--version",
        action="store_true",
        help="print the online-judge-tools version number",
    )

    subparsers = parser.add_subparsers(dest="subcommand")

    subparser = subparsers.add_parser(
        "verify",
        help="Verify library",
    )
    verify.argument_verify(subparser)

    subparser = subparsers.add_parser(
        "docs",
        help="Create documents",
    )
    docs.argument_docs(subparser)

    subparser = subparsers.add_parser(
        "download",
        help="Download problems",
    )
    download.argument_download(subparser)

    subparser = subparsers.add_parser(
        "merge-result",
        help="Merge result of`verify`",
    )
    merge_result.argument_merge_result(subparser)

    return parser


def main(args: Optional[list[str]] = None):
    import competitive_verifier.documents.main as docs
    import competitive_verifier.download.main as download
    import competitive_verifier.merge_result.main as merge_result
    import competitive_verifier.verify.main as verify
    from competitive_verifier.log import configure_logging

    parser = get_parser()
    parsed = parser.parse_args(args)

    if parsed.version:
        print(importlib.metadata.version("competitive-verifier"))
        sys.exit(0)

    default_level = INFO
    if parsed.verbose:
        default_level = DEBUG

    # Use sys.stdout for result
    if parsed.subcommand == "merge-result":
        sys.exit(0 if merge_result.run(parsed) else 1)

    configure_logging(default_level=default_level)

    logger.info("Project root: %s", str(pathlib.Path.cwd().resolve(strict=True)))

    os.chdir(orig_directory)
    args_dict = vars(parsed)
    for k, v in args_dict.items():
        if isinstance(v, pathlib.Path):
            args_dict[k] = v.resolve()
    os.chdir(root)

    # Use sys.stdout for logging
    if parsed.subcommand == "download":
        sys.exit(0 if download.run(parsed) else 1)
    elif parsed.subcommand == "verify":
        sys.exit(0 if verify.run(parsed) else 1)
    elif parsed.subcommand == "docs":
        sys.exit(0 if docs.run(parsed) else 1)


if __name__ == "__main__":
    main()
