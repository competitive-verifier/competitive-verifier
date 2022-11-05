import argparse
import logging
import sys
from logging import getLogger
from typing import Iterable, Optional

from competitive_verifier import oj
from competitive_verifier.arg import add_verify_files_json_argument
from competitive_verifier.error import VerifierError
from competitive_verifier.log import configure_logging
from competitive_verifier.models.command import ProblemVerificationCommand
from competitive_verifier.models.file import VerificationInput

logger = getLogger(__name__)


def run_impl(input: VerificationInput) -> None:
    for url in enumerate_urls(input):
        oj.download(url)


def enumerate_urls(input: VerificationInput) -> Iterable[str]:
    for f in input.files.values():
        for verification_command in f.verification:
            if isinstance(verification_command, ProblemVerificationCommand):
                yield verification_command.problem


def run(args: argparse.Namespace) -> None:
    logger.debug("arguments=%s", vars(args))
    logger.info("verify_files_json=%s", str(args.verify_files_json))
    verification = VerificationInput.parse_file(args.verify_files_json)

    return run_impl(verification)


def argument_download(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    add_verify_files_json_argument(parser)
    return parser


def main(args: Optional[list[str]] = None) -> None:
    try:
        configure_logging(logging.INFO)
        parsed = argument_download(argparse.ArgumentParser()).parse_args(args)
        run(parsed)
    except (VerifierError) as e:
        sys.stderr.write(e.message)
        sys.exit(2)


if __name__ == "__main__":
    main()
