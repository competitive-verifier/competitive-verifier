import argparse
import logging
import pathlib
import sys
from logging import getLogger
from typing import Optional

import competitive_verifier.config as config
import competitive_verifier.merge_result.main as merge_result
from competitive_verifier.arg import (
    add_ignore_error_argument,
    add_include_exclude_argument,
    add_result_json_argument,
    add_verbose_argument,
    add_verify_files_json_argument,
    add_write_summary_argument,
)
from competitive_verifier.log import configure_stderr_logging
from competitive_verifier.models import VerificationInput, VerifyCommandResult

from .. import config as conf
from .builder import DocumentBuilder

logger = getLogger(__name__)


def get_default_docs_dir() -> pathlib.Path:
    default_docs_dir = conf.get_config_dir() / "docs"
    oj_verify_docs_dir = pathlib.Path(".verify-helper/docs")
    if not default_docs_dir.exists() and oj_verify_docs_dir.exists():
        return oj_verify_docs_dir
    return default_docs_dir


def run_impl(
    input: VerificationInput,
    result: VerifyCommandResult,
    *,
    destination_dir: pathlib.Path,
    docs_dir: Optional[pathlib.Path],
    include: Optional[list[str]],
    exclude: Optional[list[str]],
) -> bool:
    logger.debug("input=%s", input.model_dump_json(exclude_none=True))
    logger.debug("result=%s", result.model_dump_json(exclude_none=True))
    builder = DocumentBuilder(
        input=input,
        result=result,
        docs_dir=docs_dir or get_default_docs_dir(),
        destination_dir=destination_dir,
        include=include,
        exclude=exclude,
    )
    return builder.build()


def run(args: argparse.Namespace) -> bool:
    default_level = logging.INFO
    if args.verbose:
        default_level = logging.DEBUG
    configure_stderr_logging(default_level)

    logger.debug("arguments=%s", vars(args))
    logger.info("verify_files_json=%s", str(args.verify_files_json))
    logger.info("result_json=%s", [str(p) for p in args.result_json])

    input = VerificationInput.parse_file_relative(args.verify_files_json)
    result = merge_result.run_impl(
        *args.result_json,
        write_summary=args.write_summary,
    )
    return (
        run_impl(
            input,
            result,
            docs_dir=args.docs,
            destination_dir=args.destination,
            include=args.include,
            exclude=args.exclude,
        )
        or args.ignore_error
    )


def argument(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    add_verbose_argument(parser)
    add_verify_files_json_argument(parser)
    add_result_json_argument(parser)
    add_ignore_error_argument(parser)
    add_write_summary_argument(parser)
    add_include_exclude_argument(parser)

    destination = config.get_config_dir() / "_jekyll"
    parser.add_argument(
        "--docs",
        type=pathlib.Path,
        help=f"Document settings directory. default: {get_default_docs_dir().as_posix()}",
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
        parsed = argument(argparse.ArgumentParser()).parse_args(args)
        if not run(parsed):
            sys.exit(1)
    except Exception as e:
        sys.stderr.write(str(e))
        sys.exit(2)
