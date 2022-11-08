import argparse
import logging
import sys
from logging import getLogger
from typing import Optional

import competitive_verifier.merge_result.main as merge_result
from competitive_verifier.arg import add_verify_files_json_argument
from competitive_verifier.log import configure_logging
from competitive_verifier.models import VerificationInput, VerifyCommandResult

logger = getLogger(__name__)


def run_impl(input: VerificationInput, result: VerifyCommandResult) -> bool:
    logger.debug("input=%s", input.json())
    logger.debug("result=%s", result.json())
    return True


def run(args: argparse.Namespace) -> bool:
    logger.debug("arguments=%s", vars(args))
    logger.info("verify_files_json=%s", str(args.verify_files_json))
    logger.info("result_json=%s", [str(p) for p in args.result_json])

    input = VerificationInput.parse_file(args.verify_files_json)
    result = merge_result.run_impl(args.result_json)
    return run_impl(input, result)


def argument_docs(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    add_verify_files_json_argument(parser)
    merge_result.argument_merge_result(parser)
    return parser


def main(args: Optional[list[str]] = None) -> None:
    try:
        configure_logging(logging.INFO)
        parsed = argument_docs(argparse.ArgumentParser()).parse_args(args)
        if not run(parsed):
            sys.exit(1)
    except Exception as e:
        sys.stderr.write(str(e))
        sys.exit(2)
