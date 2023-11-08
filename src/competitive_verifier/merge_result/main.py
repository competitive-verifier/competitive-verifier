import argparse
import logging
import pathlib
import sys
from functools import reduce
from logging import getLogger
from typing import Iterable, Optional

from competitive_verifier import github, summary
from competitive_verifier.arg import (
    add_result_json_argument,
    add_verbose_argument,
    add_write_summary_argument,
)
from competitive_verifier.log import configure_stderr_logging
from competitive_verifier.models import VerifyCommandResult

logger = getLogger(__name__)


def merge(results: Iterable[VerifyCommandResult]) -> VerifyCommandResult:
    return reduce(lambda a, b: a.merge(b), results)


def run_impl(
    *result_json: pathlib.Path,
    write_summary: bool = False,
) -> VerifyCommandResult:
    configure_stderr_logging()
    result = merge(map(VerifyCommandResult.parse_file_relative, result_json))
    if write_summary:
        gh_summary_path = github.env.get_step_summary_path()
        if gh_summary_path and gh_summary_path.parent.exists():
            with open(gh_summary_path, "w", encoding="utf-8") as fp:
                summary.write_summary(fp, result)
        else:
            logger.warning("write_summary=True but not found $GITHUB_STEP_SUMMARY")
    return result


def run(args: argparse.Namespace) -> bool:
    default_level = logging.INFO
    if args.verbose:
        default_level = logging.DEBUG
    configure_stderr_logging(default_level)

    merged = run_impl(*args.result_json, write_summary=args.write_summary)
    print(merged.model_dump_json(exclude_none=True))
    return True


def argument(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    add_verbose_argument(parser)
    add_result_json_argument(parser)
    add_write_summary_argument(parser)
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
