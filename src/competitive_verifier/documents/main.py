import argparse
import logging
import pathlib
import sys
from logging import getLogger
from typing import Optional

import competitive_verifier.merge_result.main as merge_result
from competitive_verifier.arg import (
    add_ignore_error_argument,
    add_result_json_argument,
    add_verify_files_json_argument,
    add_write_summary_argument,
)
from competitive_verifier.config import config_dir
from competitive_verifier.log import configure_logging
from competitive_verifier.models import VerificationInput, VerifyCommandResult

from .builder import DocumentBuilder

logger = getLogger(__name__)


def run_impl(
    input: VerificationInput,
    result: VerifyCommandResult,
    docs_dir: Optional[pathlib.Path],
    destination_dir: pathlib.Path,
    ignore_error: bool,
) -> bool:
    logger.debug("input=%s", input.json())
    logger.debug("result=%s", result.json())
    builder = DocumentBuilder(input, result, docs_dir, destination_dir)
    return builder.build() or ignore_error


def run(args: argparse.Namespace) -> bool:
    logger.debug("arguments=%s", vars(args))
    logger.info("verify_files_json=%s", str(args.verify_files_json))
    logger.info("result_json=%s", [str(p) for p in args.result_json])

    input = VerificationInput.parse_file_relative(args.verify_files_json)
    result = merge_result.run_impl(
        *args.result_json,
        write_summary=args.write_summary,
    )
    return run_impl(input, result, args.docs, args.destination, args.ignore_error)


def argument(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    add_verify_files_json_argument(parser)
    add_result_json_argument(parser)
    add_ignore_error_argument(parser)
    add_write_summary_argument(parser)
    destination = config_dir / "_jekyll"
    docs = config_dir / "docs"
    parser.add_argument(
        "--docs",
        type=pathlib.Path,
        help=f"Document settings directory. default: {docs.as_posix()}",
    )
    parser.add_argument(
        "--destination",
        type=pathlib.Path,
        default=destination,
        help=f"Output directory for markdown document. default: {destination.as_posix()}",
    )
    return parser


def main(args: Optional[list[str]] = None) -> None:
    try:
        configure_logging(logging.INFO)
        parsed = argument(argparse.ArgumentParser()).parse_args(args)
        if not run(parsed):
            sys.exit(1)
    except Exception as e:
        sys.stderr.write(str(e))
        sys.exit(2)
