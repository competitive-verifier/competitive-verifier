import argparse
import json
import pathlib
import platform
from logging import getLogger
from typing import Optional

import onlinejudge_command.format_utils as fmtutils
import onlinejudge_command.utils as utils
from onlinejudge_command.subcommand.test import (
    JudgeStatus,
    check_gnu_time,
    test_single_case,
)
from pydantic import BaseModel

logger = getLogger(__name__)


class TestCase(BaseModel):
    name: str
    input: pathlib.Path
    output: Optional[pathlib.Path] = None


class OjTestcaseResult(BaseModel):
    status: JudgeStatus
    elapsed: float
    memory: Optional[float] = None
    exitcode: int
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
    if not check_gnu_time(args.gnu_time):
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
                test_single_case(name, paths["in"], paths.get("out"), args=args),
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
        if result.status == JudgeStatus.AC:
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
