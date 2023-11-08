import argparse
import logging
import sys
from logging import getLogger
from typing import Optional

from competitive_verifier.arg import add_verbose_argument
from competitive_verifier.log import configure_stderr_logging

from . import migration

logger = getLogger(__name__)


def run_impl(dry_run: bool) -> bool:
    return migration.main(dry_run)


def run(args: argparse.Namespace) -> bool:
    default_level = logging.INFO
    if args.verbose:
        default_level = logging.DEBUG
    configure_stderr_logging(default_level)

    logger.debug("arguments=%s", vars(args))
    return run_impl(args.dry_run)


def argument(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    add_verbose_argument(parser)
    parser.add_argument(
        "--dry-run",
        "-n",
        dest="dry_run",
        action="store_true",
        help="Run a trial migration with no changes. Just show logs only.",  # noqa: E501
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


if __name__ == "__main__":
    main()
