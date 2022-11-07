import argparse
import logging
import sys
from typing import Optional

from competitive_verifier.arg import add_verify_files_json_argument
from competitive_verifier.log import configure_logging
from competitive_verifier.models.result import VerifyCommandResult


def run_impl(verification: VerifyCommandResult) -> bool:
    raise NotImplementedError()


def run(args: argparse.Namespace) -> bool:
    raise NotImplementedError()


def argument_docs(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    add_verify_files_json_argument(parser)
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
