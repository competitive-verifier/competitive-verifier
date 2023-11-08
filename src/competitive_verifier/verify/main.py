import argparse
import logging
import math
import pathlib
import sys
from logging import getLogger
from typing import Optional

from competitive_verifier import github, summary
from competitive_verifier.arg import (
    add_ignore_error_argument,
    add_verbose_argument,
    add_verify_files_json_argument,
    add_write_summary_argument,
)
from competitive_verifier.error import VerifierError
from competitive_verifier.log import configure_stderr_logging
from competitive_verifier.models import VerificationInput, VerifyCommandResult
from competitive_verifier.verify.verifier import SplitState, Verifier

logger = getLogger(__name__)


def run_impl(
    input: VerificationInput,
    *,
    prev_result: Optional[VerifyCommandResult],
    timeout: float = math.inf,
    default_tle: Optional[float] = None,
    default_mle: Optional[float] = None,
    download: bool = True,
    split: Optional[int] = None,
    split_index: Optional[int] = None,
    output_path: Optional[pathlib.Path] = None,
    write_summary: bool = False,
    ignore_error: bool = False,
) -> bool:
    split_state = get_split_state(split, split_index)

    if timeout == 0:
        timeout = math.inf

    verifier = Verifier(
        input,
        use_git_timestamp=github.env.is_in_github_actions(),
        timeout=timeout,
        default_tle=default_tle,
        default_mle=default_mle,
        prev_result=prev_result,
        split_state=split_state,
    )
    result = verifier.verify(download=download)
    result_json = result.model_dump_json(exclude_none=True)

    if write_summary:
        gh_summary_path = github.env.get_step_summary_path()
        if gh_summary_path and gh_summary_path.parent.exists():
            with open(gh_summary_path, "w", encoding="utf-8") as fp:
                summary.write_summary(fp, result)
        else:
            logger.warning("write_summary=True but not found $GITHUB_STEP_SUMMARY")

    print(result_json)

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(result_json, encoding="utf-8")

    is_success = result.is_success()

    if is_success:
        logger.info("success!")
    else:
        logger.warning("not success!")

    return is_success or ignore_error


def run(args: argparse.Namespace) -> bool:
    default_level = logging.INFO
    if args.verbose:
        default_level = logging.DEBUG
    configure_stderr_logging(default_level)

    logger.debug("arguments=%s", vars(args))
    logger.info("verify_files_json=%s", str(args.verify_files_json))
    input = VerificationInput.parse_file_relative(args.verify_files_json)
    prev_result = None
    if args.prev_result:
        try:
            prev_result = VerifyCommandResult.parse_file_relative(args.prev_result)
        except Exception:
            logger.warning("Failed to parse prev_result: %s", args.prev_result)

    return run_impl(
        input,
        timeout=args.timeout,
        default_tle=args.default_tle,
        default_mle=args.default_mle,
        prev_result=prev_result,
        download=args.download,
        split=args.split,
        split_index=args.split_index,
        output_path=args.output,
        write_summary=args.write_summary,
        ignore_error=args.ignore_error,
    )


def argument(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    add_verbose_argument(parser)
    add_verify_files_json_argument(parser)
    add_ignore_error_argument(parser)
    add_write_summary_argument(parser)
    parser.add_argument(
        "--timeout",
        type=float,
        default=math.inf,
        help="Timeout seconds. if value is zero, it is same to math.inf.",
    )
    parser.add_argument(
        "--tle",
        dest="default_tle",
        type=float,
        default=None,
        help="Threshold seconds to be TLE",
    )
    parser.add_argument(
        "--mle",
        dest="default_mle",
        type=float,
        default=None,
        help="Threshold memory usage (MB) to be MLE",
    )
    parser.add_argument(
        "--prev-result",
        type=pathlib.Path,
        required=False,
        help="Previous result json file",
    )

    parser.add_argument(
        "--no-download",
        action="store_false",
        dest="download",
        help="Suppress `oj download`",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=pathlib.Path,
        required=False,
        help="The output file for which verifier saves the result json.",
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
            raise VerifierError("--split must be greater than 0.")
        if not (0 <= split_index < split):
            raise VerifierError(
                "--split-index must be greater than 0 and less than --split."
            )
        return SplitState(size=split, index=split_index)

    if split is not None:
        raise VerifierError("--split argument requires --split-index argument.")

    if split_index is not None:
        raise VerifierError("--split-index argument requires --split argument.")

    raise VerifierError("invalid state.")


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
