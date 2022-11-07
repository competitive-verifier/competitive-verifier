import argparse
import pathlib
import sys
from functools import reduce
from typing import Iterable, Optional

from competitive_verifier.models import VerificationResult


def merge(results: Iterable[VerificationResult]) -> VerificationResult:
    return reduce(lambda a, b: a.merge(b), results)


def run_impl(result_json: Iterable[pathlib.Path]) -> VerificationResult:
    return merge(map(VerificationResult.parse_file, result_json))


def run(args: argparse.Namespace) -> bool:
    merged = run_impl(args.result_json)
    print(merged.json())
    return True


def argument_merge_result(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    parser.add_argument(
        "result_json",
        nargs="+",
        help="Json files which is result of `verify`",
        type=pathlib.Path,
    )
    return parser


def main(args: Optional[list[str]] = None) -> None:
    try:
        parsed = argument_merge_result(argparse.ArgumentParser()).parse_args(args)
        if not run(parsed):
            sys.exit(1)
    except Exception as e:
        sys.stderr.write(str(e))
        sys.exit(2)


if __name__ == "__main__":
    main()
