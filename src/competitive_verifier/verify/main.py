import argparse
import json
import pathlib
import sys
from logging import getLogger
from typing import Optional

from competitive_verifier.log import configure_logging
from competitive_verifier.models import (
    VerificationFiles,
    VerificationResult,
    decode_verification_files,
)

logger = getLogger(__name__)


def run_impl(
    files: VerificationFiles, *, timeout: float = 1800, default_tle: float = 60
) -> VerificationResult:
    logger.info(files.__dict__)
    return VerificationResult(file_results=[])


def run(args: argparse.Namespace) -> VerificationResult:
    with open(args.verify_files_json, encoding="utf-8") as f:
        files = decode_verification_files(json.load(f))
        return run_impl(files, timeout=args.timeout, default_tle=args.default_tle)


def argument_verify(
    parser: argparse.ArgumentParser,
    *,
    default_json: Optional[pathlib.Path] = None,
) -> argparse.ArgumentParser:
    if default_json is None:
        parser.add_argument(
            "verify_files_json",
            help="File path of verify_files.json.",
            type=pathlib.Path,
        )
    else:
        parser.add_argument(
            "verify_files_json",
            nargs="?",
            default=default_json,
            help='File path of verify_files.json. default: "{}"'.format(default_json),
            type=pathlib.Path,
        )

    parser.add_argument("--timeout", dest="timeout", type=float, default=1800)
    parser.add_argument("--tle", dest="default_tle", type=float, default=60)
    return parser


def main(args: Optional[list[str]] = None) -> None:
    configure_logging()
    parsed = argument_verify(argparse.ArgumentParser()).parse_args(args)
    verification = run(parsed)
    if not verification.is_success():
        sys.exit(1)


if __name__ == "__main__":
    main()
