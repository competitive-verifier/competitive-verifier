import argparse
import json
import math
import pathlib
import sys
from logging import getLogger
from typing import Optional

from competitive_verifier import github
from competitive_verifier.log import configure_logging
from competitive_verifier.models.file import (
    VerificationInput,
    decode_verification_files,
)
from competitive_verifier.models.result import VerificationResult, decode_result_json
from competitive_verifier.verify.util import VerifyError
from competitive_verifier.verify.verifier import SplitState, Verifier

logger = getLogger(__name__)


def run_impl(
    verification: VerificationInput,
    *,
    prev_result: Optional[VerificationResult],
    timeout: float = 1800,
    default_tle: float = math.inf,
    split: Optional[int] = None,
    split_index: Optional[int] = None,
) -> Verifier:
    split_state = get_split_state(split, split_index)
    verifier = Verifier(
        verification,
        use_git_timestamp=github.is_in_github_actions(),
        timeout=timeout,
        default_tle=default_tle,
        prev_result=prev_result,
        split_state=split_state,
    )
    for f in verification.files:
        logger.info({"file": f.path, "time": verifier.get_current_timestamp(f.path)})
    return verifier


def run(args: argparse.Namespace) -> Verifier:
    with open(args.verify_files_json, encoding="utf-8") as f:
        verification = decode_verification_files(json.load(f))
    if args.prev_result is None:
        prev_result = None
    else:
        with open(args.prev_result, encoding="utf-8") as f:
            prev_result = decode_result_json(json.load(f))
    return run_impl(
        verification,
        timeout=args.timeout,
        default_tle=args.default_tle,
        prev_result=prev_result,
        split=args.split,
        split_index=args.split_index,
    )


def argument_verify(
    parser: argparse.ArgumentParser,
    *,
    default_json: Optional[pathlib.Path] = None,
) -> argparse.ArgumentParser:
    if default_json is None:
        parser.add_argument(
            "verify_files_json",
            help="File path of verify_files.json.",
            type=pathlib.Path,
        )
    else:
        parser.add_argument(
            "verify_files_json",
            nargs="?",
            default=default_json,
            help='File path of verify_files.json. default: "{}"'.format(default_json),
            type=pathlib.Path,
        )

    parser.add_argument(
        "--timeout",
        type=float,
        default=math.inf,
        help="Timeout",
    )
    parser.add_argument(
        "--tle",
        dest="default_tle",
        type=float,
        default=60,
        help="TLE threshold seconds",
    )
    parser.add_argument(
        "--prev-result",
        type=pathlib.Path,
        required=False,
        help="Previout result json path",
    )

    parser.add_argument_group()
    parallel_group = parser.add_argument_group("parallel")
    parallel_group.add_argument(
        "--split",
        type=int,
        help="Parallel job size",
        required=False,
    )
    parallel_group.add_argument(
        "--split-index",
        type=int,
        help="Parallel job index",
        required=False,
    )

    return parser


def get_split_state(
    split: Optional[int] = None,
    split_index: Optional[int] = None,
) -> Optional[SplitState]:
    if split_index is None and split is None:
        return None

    if split_index is not None and split is not None:
        if split <= 0:
            raise VerifyError("--split must be greater than 0.")
        if not (0 <= split_index < split):
            raise VerifyError(
                "--split-index must be greater than 0 and less than --split."
            )
        return SplitState(size=split, index=split_index)

    if split is not None:
        raise VerifyError("--split argument requires --split-index argument.")

    if split_index is not None:
        raise VerifyError("--split-index argument requires --split argument.")

    raise VerifyError("invalid state.")


def main(args: Optional[list[str]] = None) -> None:
    configure_logging()
    parsed = argument_verify(argparse.ArgumentParser()).parse_args(args)
    verifier = run(parsed)
    if not verifier.is_success():
        sys.exit(1)


if __name__ == "__main__":
    main()
