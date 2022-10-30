import argparse
import pathlib
import sys
from typing import Optional

from competitive_verifier.utils import VerificationSummary


def run(args: argparse.Namespace) -> VerificationSummary:
    return VerificationSummary(failed_test_paths=[])


def argument_verify(parser: argparse.ArgumentParser, *, default_json: Optional[pathlib.Path] = None) -> argparse.ArgumentParser:
    if default_json is None:
        parser.add_argument(
            'verify_files_json',
            help='File path of verify_files.json.',
            type=pathlib.Path
        )
    else:
        parser.add_argument(
            'verify_files_json',
            nargs='?',
            default=default_json,
            help='File path of verify_files.json. default: "{}"'.format(
                default_json
            ),
            type=pathlib.Path
        )

    parser.add_argument(
        '--timeout',
        dest='default_timeout',
        type=float, default=1800
    )
    parser.add_argument(
        '--tle',
        dest='default_tle',
        type=float, default=60
    )
    return parser


def main(args: Optional[list[str]] = None) -> None:
    parsed = argument_verify(argparse.ArgumentParser()).parse_args(args)
    summary = run(parsed)
    if not summary.succeeded():
        sys.exit(1)


if __name__ == "__main__":
    main()
