import argparse
import json
import pathlib
import sys
from logging import getLogger
from typing import Iterable, Optional

from competitive_verifier import oj
from competitive_verifier.error import VerifierError
from competitive_verifier.log import configure_logging
from competitive_verifier.models.command import ProblemVerificationCommand
from competitive_verifier.models.file import (
    VerificationInput,
    decode_verification_files,
)

logger = getLogger(__name__)


def run_impl(urls: Iterable[str]) -> None:
    for url in urls:
        oj.download(url)


def enumerate_urls(input: VerificationInput) -> Iterable[str]:
    for f in input.files:
        if isinstance(f.verification, ProblemVerificationCommand):
            yield f.verification.problem


def run(args: argparse.Namespace) -> None:
    logger.info("arguments=%s", vars(args))
    with open(args.verify_files_json, encoding="utf-8") as f:
        verification = decode_verification_files(json.load(f))

    return run_impl(enumerate_urls(verification))


def argument_download(
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
    return parser


def main(args: Optional[list[str]] = None) -> None:
    try:
        configure_logging()
        parsed = argument_download(argparse.ArgumentParser()).parse_args(args)
        run(parsed)
    except (VerifierError) as e:
        sys.stderr.write(e.message)
        sys.exit(2)


if __name__ == "__main__":
    main()
