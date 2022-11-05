import argparse
import logging
from typing import Optional

from competitive_verifier.arg import add_verify_files_json_argument
from competitive_verifier.log import configure_logging
from competitive_verifier.models.result import VerificationResult


def run_impl(verification: VerificationResult) -> None:
    pass


def run(args: argparse.Namespace) -> None:
    pass


def argument_docs(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    add_verify_files_json_argument(parser)
    return parser


def main(args: Optional[list[str]] = None) -> None:
    configure_logging(logging.INFO)
    parsed = argument_docs(argparse.ArgumentParser()).parse_args(args)
    run(parsed)
