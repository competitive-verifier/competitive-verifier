import argparse
import os
import pathlib
import sys
import textwrap
from logging import INFO, basicConfig, getLogger
from typing import Optional

import colorlog

import competitive_verifier.documents.main as docs
import competitive_verifier.verify.main as verify

_config_directory_name = '.competitive-verifier'
logger = getLogger(__name__)


def configure_logging() -> None:
    log_format = '%(log_color)s%(levelname)s%(reset)s:%(name)s:%(message)s'
    handler = colorlog.StreamHandler()
    handler.setFormatter(colorlog.ColoredFormatter(log_format))
    basicConfig(level=INFO, handlers=[handler])


def find_project_root_directory() -> Optional[pathlib.Path]:
    dir = pathlib.Path(os.getcwd())
    if (dir / _config_directory_name).exists():
        return dir
    for dir in dir.parents:
        if (dir / _config_directory_name).exists():
            return dir
    return None


def generate_gitignore() -> None:
    dir_path = pathlib.Path('.verify-helper')
    if dir_path.exists():
        return
    dir_path.mkdir(parents=True, exist_ok=True)

    gitignore_path = dir_path / '.gitignore'
    data = textwrap.dedent("""\
        cache/
        timestamps.local.json
    """)
    with open(gitignore_path, 'w') as fh:
        fh.write(data)


def get_parser() -> argparse.ArgumentParser:
    default_verify_files_json = pathlib.Path(
        f'{_config_directory_name}/verify_files.json'
    )

    default_verify_result_json = pathlib.Path(
        f'{_config_directory_name}/verify_result.json'
    )

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='subcommand')

    subparser = subparsers.add_parser('verify')
    verify.argument_verify(subparser, default_json=default_verify_files_json)

    subparser = subparsers.add_parser('docs')
    docs.argument_docs(subparser, default_json=default_verify_result_json)

    subparser = subparsers.add_parser('all')
    verify.argument_verify(subparser, default_json=default_verify_files_json)
    return parser


def parse_args(args: Optional[list[str]]) -> argparse.Namespace:
    return get_parser().parse_args(args)


def main(args: Optional[list[str]] = None):
    # Move to directory which contains .competitive-verifier/
    root = find_project_root_directory()
    if root is not None:
        os.chdir(root)

    parsed = parse_args(args)
    configure_logging()

    generate_gitignore()

    summary = verify.run(parsed)
    docs.run_impl(summary)

    if not summary.succeeded():
        sys.exit(1)


if __name__ == "__main__":
    main()
