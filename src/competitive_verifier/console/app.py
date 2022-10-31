import argparse
import os
import pathlib
import sys
from logging import getLogger
from typing import Optional

import competitive_verifier.documents.main as docs
import competitive_verifier.verify.main as verify
from competitive_verifier.log import configure_logging

_config_directory_name = ".competitive-verifier"
logger = getLogger(__name__)


def find_project_root_directory() -> Optional[pathlib.Path]:
    dir = pathlib.Path.cwd()
    if (dir / _config_directory_name).exists():
        return dir
    for dir in dir.parents:
        if (dir / _config_directory_name).exists():
            return dir
    return None


def get_parser() -> argparse.ArgumentParser:
    default_verify_files_json = pathlib.Path(
        f"{_config_directory_name}/verify_files.json"
    )

    default_verify_result_json = pathlib.Path(
        f"{_config_directory_name}/verify_result.json"
    )

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="subcommand")

    subparser = subparsers.add_parser("verify")
    verify.argument_verify(subparser, default_json=default_verify_files_json)

    subparser = subparsers.add_parser("docs")
    docs.argument_docs(subparser, default_json=default_verify_result_json)

    return parser


def main(args: Optional[list[str]] = None):
    # Move to directory which contains .competitive-verifier/
    root = find_project_root_directory()
    if root is not None:
        os.chdir(root)

    configure_logging()

    logger.info("Project root: %s", str(pathlib.Path.cwd().resolve(strict=True)))
    parser = get_parser()
    parsed = parser.parse_args(args)

    verifier = verify.run(parsed)
    docs.run_impl(verifier.force_result)

    if not verifier.is_success():
        sys.exit(1)


if __name__ == "__main__":
    main()
