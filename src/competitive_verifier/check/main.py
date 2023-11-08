import argparse
import logging
import pathlib
import sys
from collections import Counter
from functools import reduce
from logging import getLogger
from typing import Iterable, Optional

from competitive_verifier.arg import add_result_json_argument, add_verbose_argument
from competitive_verifier.log import configure_stderr_logging
from competitive_verifier.models import ResultStatus, VerifyCommandResult

logger = getLogger(__name__)


def merge(results: Iterable[VerifyCommandResult]) -> VerifyCommandResult:
    return reduce(lambda a, b: a.merge(b), results)


def run_impl(*result_json: pathlib.Path) -> bool:
    configure_stderr_logging()

    result = merge(map(VerifyCommandResult.parse_file_relative, result_json))

    counter = Counter(
        r.status for fr in result.files.values() for r in fr.verifications
    )

    for st in ResultStatus:
        print(f"{st.value}: {counter.get(st, 0)}")

    if counter[ResultStatus.FAILURE] > 0:
        logger.error("Failure test count: %d", counter[ResultStatus.FAILURE])
        return False
    return True


def run(args: argparse.Namespace) -> bool:
    default_level = logging.INFO
    if args.verbose:
        default_level = logging.DEBUG
    configure_stderr_logging(default_level)

    return run_impl(*args.result_json)


def argument(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    add_verbose_argument(parser)
    add_result_json_argument(parser)
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
