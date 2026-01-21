import argparse
import logging
import pathlib
from collections.abc import Iterable
from functools import reduce
from logging import getLogger

from competitive_verifier.arg import add_verbose_argument
from competitive_verifier.log import configure_stderr_logging
from competitive_verifier.models import VerificationInput

logger = getLogger(__name__)


def merge(inputs: Iterable[VerificationInput]) -> VerificationInput:
    return reduce(lambda a, b: a.merge(b), inputs)


def run_impl(
    *verify_files_json: pathlib.Path,
) -> VerificationInput:
    configure_stderr_logging()
    return merge(map(VerificationInput.parse_file_relative, verify_files_json))


def run(args: argparse.Namespace) -> bool:
    default_level = logging.INFO
    if args.verbose:
        default_level = logging.DEBUG
    configure_stderr_logging(default_level)

    merged = run_impl(*args.verify_files_json)
    print(merged.model_dump_json(exclude_none=True))
    return True


def argument(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    add_verbose_argument(parser)
    parser.add_argument(
        "verify_files_json",
        nargs="+",
        help="verify_files.json files",
        type=pathlib.Path,
    )
    return parser
