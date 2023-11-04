import argparse
import json
import pathlib
import platform
import subprocess
from logging import getLogger
from typing import Annotated, Any, Optional

import onlinejudge_command.format_utils as fmtutils
import onlinejudge_command.pretty_printers as pretty_printers
import onlinejudge_command.subcommand.test as oj_test
import onlinejudge_command.utils as utils
from onlinejudge_command.subcommand.test import DisplayMode, JudgeStatus
from pydantic import BaseModel
from pydantic.functional_validators import BeforeValidator

logger = getLogger(__name__)


# flake8: noqa: C901
def display_result(
    proc: subprocess.Popen[Any],
    answer: str,
    memory: Optional[float],
    test_input_path: pathlib.Path,
    test_output_path: Optional[pathlib.Path],
    *,
    mle: Optional[float],
    display_mode: DisplayMode,
    compare_mode: oj_test.CompareMode,
    does_print_input: bool,
    silent: bool,
    match_result: Optional[bool],
) -> JudgeStatus:
    """display_result prints the result of the test and its statistics.

    This function prints many logs and does some I/O.
    """

    # prepare the function to print the input
    is_input_printed = False

    def print_input() -> None:
        nonlocal is_input_printed
        if does_print_input and not is_input_printed:
            is_input_printed = True
            with test_input_path.open("rb") as inf:
                logger.info(
                    utils.NO_HEADER + "input:\n%s",
                    pretty_printers.make_pretty_large_file_content(
                        inf.read(), limit=40, head=20, tail=10
                    ),
                )

    # check TLE, RE or not
    status = JudgeStatus.AC
    if proc.returncode is None:
        logger.info(utils.FAILURE + "" + utils.red("TLE"))
        status = JudgeStatus.TLE
        if not silent:
            print_input()
    elif memory is not None and mle is not None and memory > mle:
        logger.info(utils.FAILURE + "" + utils.red("MLE"))
        status = JudgeStatus.MLE
        if not silent:
            print_input()
    elif proc.returncode != 0:
        logger.info(
            utils.FAILURE + "" + utils.red("RE") + ": return code %d", proc.returncode
        )
        status = JudgeStatus.RE
        if not silent:
            print_input()

    # check WA or not
    # 元の実装では TLE や RE でもこっちに来てしまうので elif に変更
    elif match_result is not None and not match_result:
        if status == JudgeStatus.AC:
            logger.info(utils.FAILURE + "" + utils.red("WA"))
        status = JudgeStatus.WA
        if not silent:
            print_input()
            if test_output_path is not None:
                with test_output_path.open("rb") as outf:
                    expected = outf.read().decode()
            else:
                expected = ""
            if display_mode == DisplayMode.SUMMARY:
                logger.info(
                    utils.NO_HEADER + "output:\n%s",
                    pretty_printers.make_pretty_large_file_content(
                        answer.encode(), limit=40, head=20, tail=10
                    ),
                )
                logger.info(
                    utils.NO_HEADER + "expected:\n%s",
                    pretty_printers.make_pretty_large_file_content(
                        expected.encode(), limit=40, head=20, tail=10
                    ),
                )
            elif display_mode == DisplayMode.ALL:
                logger.info(
                    utils.NO_HEADER + "output:\n%s",
                    pretty_printers.make_pretty_all(answer.encode()),
                )
                logger.info(
                    utils.NO_HEADER + "expected:\n%s",
                    pretty_printers.make_pretty_all(expected.encode()),
                )
            elif display_mode == DisplayMode.DIFF:
                logger.info(
                    utils.NO_HEADER
                    + pretty_printers.make_pretty_diff(
                        answer.encode(),
                        expected=expected,
                        compare_mode=compare_mode,
                        limit=40,
                    )
                )
            elif display_mode == DisplayMode.DIFF_ALL:
                logger.info(
                    utils.NO_HEADER
                    + pretty_printers.make_pretty_diff(
                        answer.encode(),
                        expected=expected,
                        compare_mode=compare_mode,
                        limit=-1,
                    )
                )
            else:
                assert False
    if match_result is None:
        if not silent:
            print_input()
            logger.info(
                utils.NO_HEADER + "output:\n%s",
                pretty_printers.make_pretty_large_file_content(
                    answer.encode(), limit=40, head=20, tail=10
                ),
            )
    if status == JudgeStatus.AC:
        logger.info(utils.SUCCESS + "" + utils.green("AC"))

    return status


oj_test.display_result = display_result


class TestCase(BaseModel):
    name: str
    input: pathlib.Path
    output: Optional[pathlib.Path] = None


class OjTestcaseResult(BaseModel):
    status: oj_test.JudgeStatus
    elapsed: float
    memory: Optional[float] = None
    exitcode: Annotated[
        Optional[int], BeforeValidator(lambda v: v if isinstance(v, int) else None)
    ]
    testcase: TestCase


class OjTestResult(BaseModel):
    is_success: bool

    elapsed: float

    slowest: float
    """max time [seconds]
    """

    heaviest: float
    """max memory [MB]
    """

    testcases: list[OjTestcaseResult]


def get_gnu_time_command() -> str:
    if platform.system() == "Darwin":
        return "gtime"
    else:
        return "time"


def check_gnu_time(gnu_time: Optional[str] = None) -> bool:
    return oj_test.check_gnu_time(gnu_time or get_gnu_time_command())


def run(args: "argparse.Namespace") -> OjTestResult:
    # list tests
    if not args.test:
        args.test = fmtutils.glob_with_format(args.directory, args.format)  # by default
    if args.ignore_backup:
        args.test = fmtutils.drop_backup_or_hidden_files(args.test)
    tests = fmtutils.construct_relationship_of_files(
        args.test, args.directory, args.format
    )

    # check wheather GNU time is available
    if args.gnu_time is None:
        if platform.system() == "Darwin":
            args.gnu_time = "gtime"
        else:
            args.gnu_time = "time"
    if not oj_test.check_gnu_time(args.gnu_time):
        logger.warning("GNU time is not available: %s", args.gnu_time)
        if platform.system() == "Darwin":
            logger.info(
                utils.HINT + "You can install GNU time with: $ brew install gnu-time"
            )
        args.gnu_time = None
    if args.mle is not None and args.gnu_time is None:
        raise RuntimeError("--mle is used but GNU time does not exist")

    # run tests
    history: list[OjTestcaseResult] = []
    for name, paths in sorted(tests.items()):
        history.append(
            OjTestcaseResult.model_validate(
                oj_test.test_single_case(
                    name, paths["in"], paths.get("out"), args=args
                ),
            )
        )

    # summarize
    elapsed: float = 0.0
    slowest: float = -1.0
    slowest_name = ""
    heaviest: float = -1.0
    heaviest_name = ""
    ac_count = 0
    for result in history:
        elapsed += result.elapsed
        if result.status == oj_test.JudgeStatus.AC:
            ac_count += 1
        if slowest < result.elapsed:
            slowest = result.elapsed
            slowest_name = result.testcase.name
        if result.memory is not None and heaviest < result.memory:
            heaviest = result.memory
            heaviest_name = result.testcase.name

    # print the summary
    logger.info("")
    logger.info("slowest: %f sec  (for %s)", slowest, slowest_name)
    if heaviest >= 0:
        logger.info("max memory: %f MB  (for %s)", heaviest, heaviest_name)
    if ac_count == len(tests):
        logger.info(
            utils.SUCCESS + "test " + utils.green("success") + ": %d cases", len(tests)
        )
    else:
        logger.info(
            utils.FAILURE + "test " + utils.red("failed") + ": %d AC / %d cases",
            ac_count,
            len(tests),
        )

    if args.log_file:
        with args.log_file.open(mode="w") as fh:
            json.dump(history, fh)

    # return the result
    return OjTestResult(
        is_success=ac_count == len(tests),
        slowest=slowest,
        elapsed=elapsed,
        heaviest=heaviest,
        testcases=history,
    )
