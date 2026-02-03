import contextlib
import os
import pathlib
import platform
import shlex
import signal
import subprocess
import sys
import tempfile
import time
from collections.abc import Callable
from logging import getLogger
from typing import Annotated, BinaryIO

from pydantic import BaseModel
from pydantic.functional_validators import BeforeValidator

from competitive_verifier.models import (
    JudgeStatus,
    Problem,
    ResultStatus,
    TestcaseResult,
    VerifcationTimeoutError,
    VerificationResult,
)

from . import comparer, gnu
from .format import Printer, green, red
from .service import format_utils as fmtutils

logger = getLogger(__name__)

# logging output.
HINT = "HINT"
SUCCESS = "SUCCESS"
FAILURE = "FAILURE"


class _ExecError(Exception):
    pass


class OjExecInfo(BaseModel):
    answer: bytes | None
    """The standard output of the executed command"""
    elapsed: float
    """The elapsed time of the executed command in seconds"""
    memory: float | None
    """The maximum memory usage of the executed command in megabytes"""
    returncode: int | None
    """The returncode of the executed command"""


def measure_command(
    command: list[str] | str,
    *,
    env: dict[str, str] | None = None,
    stdin: BinaryIO | int | None = None,
    input: bytes | None = None,  # noqa: A002
    timeout: float | None = None,
    gnu_time: bool = False,
) -> OjExecInfo:
    if input is not None:
        if stdin is not None:
            raise ValueError(
                stdin, "stdin and input cannot be specified at the same time"
            )
        stdin = subprocess.PIPE

    if isinstance(command, str):
        command = shlex.split(command)
    with gnu.GnuTimeWrapper(enabled=gnu_time) as gw:
        command = gw.get_command(command)
        begin = time.perf_counter()

        # We need kill processes called from the "time" command using process groups. Without this, orphans spawn. see https://github.com/kmyk/online-judge-tools/issues/640
        start_new_session = gnu.time_command() is not None and os.name == "posix"

        try:
            if env:
                env = os.environ | env
            proc = subprocess.Popen(
                command,
                stdin=stdin,
                stdout=subprocess.PIPE,
                env=env,
                stderr=sys.stderr,
                start_new_session=start_new_session,
            )
        except FileNotFoundError as e:
            logger.exception("No such file or directory: %s", command)
            raise _ExecError from e
        except PermissionError as e:
            logger.exception("Permission denied: %s", command)
            raise _ExecError from e
        answer: bytes | None = None
        try:
            answer, _ = proc.communicate(input=input, timeout=timeout)
        except subprocess.TimeoutExpired:
            pass
        finally:
            if start_new_session:
                with contextlib.suppress(ProcessLookupError):
                    os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
            else:
                proc.terminate()

        end = time.perf_counter()
        memory: float | None = None
        report = gw.get_report()
        if report:
            logger.debug("GNU time says:\n%s", report)
            if report.splitlines()[-1].isdigit():
                memory = int(report.splitlines()[-1]) / 1000
        return OjExecInfo(
            answer=answer,
            elapsed=end - begin,
            memory=memory,
            returncode=proc.returncode,
        )


class OjTestArguments(BaseModel):
    """Parameters for oj-test command.

    Port of onlinejudge_command.subcommand.test.add_subparser.
    """

    command: str | list[str]
    directory: pathlib.Path
    tle: float | None
    mle: float | None
    error: float | None
    judge: pathlib.Path | None
    env: dict[str, str] | None = None
    deadline: float = float("inf")


def display_result(
    exitcode: int | None,
    answer: bytes,
    memory: float | None,
    test_input_path: pathlib.Path,
    test_output_path: pathlib.Path | None,
    *,
    mle: float | None,
    match_result: bool | None,
) -> JudgeStatus:
    """display_result prints the result of the test and its statistics.

    This function prints many logs and does some I/O.
    """
    # prepare the function to print the input
    is_input_printed = False

    def print_input() -> None:
        nonlocal is_input_printed
        if not is_input_printed:
            is_input_printed = True
            with test_input_path.open("rb") as inf:
                logger.info("input:\n%s", Printer(inf.read()))

    # check TLE, RE or not
    status = JudgeStatus.AC
    if exitcode is None:
        logger.info("%s: %s", FAILURE, red("TLE"))
        status = JudgeStatus.TLE
        print_input()
    elif memory is not None and mle is not None and memory > mle:
        logger.info("%s: %s", FAILURE, red("MLE"))
        status = JudgeStatus.MLE
        print_input()
    elif exitcode != 0:
        logger.info("%s: %s: return code %d", FAILURE, red("RE"), exitcode)
        status = JudgeStatus.RE
        print_input()

    # check WA or not
    # 元の実装では TLE や RE でもこっちに来てしまうので elif に変更
    elif match_result is not None and not match_result:
        if status == JudgeStatus.AC:
            logger.info("%s: %s", FAILURE, red("WA"))
        status = JudgeStatus.WA
        print_input()
        if test_output_path is not None:
            with test_output_path.open("rb") as outf:
                expected = outf.read()
        else:
            expected = ""
        logger.info("output:\n%s", Printer(answer))
        logger.info("expected:\n%s", Printer(expected))
    if match_result is None:
        print_input()
        logger.info("output:\n%s", Printer(answer))
    if status == JudgeStatus.AC:
        logger.info("%s: %s", SUCCESS, green("AC"))

    return status


class OjTestcaseResult(BaseModel):
    name: str
    """A name of test case."""
    input: pathlib.Path
    """A input of test case."""
    output: pathlib.Path | None = None
    """A output of test case."""

    status: JudgeStatus
    elapsed: float
    memory: float | None = None
    exitcode: Annotated[
        int | None, BeforeValidator(lambda v: v if isinstance(v, int) else None)
    ]


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


class SpecialJudge:
    def __init__(
        self,
        judge_command: str,
        *,
        input_path: pathlib.Path,
        expected_output_path: pathlib.Path | None,
    ):
        self.judge_command = judge_command  # already quoted and joined command
        self.input_path = input_path
        self.expected_output_path = expected_output_path

    def run(self, actual_output: bytes, _: bytes) -> bool:
        with tempfile.TemporaryDirectory() as tempdir:
            actual_output_path = pathlib.Path(tempdir) / "actual.out"
            with actual_output_path.open("wb") as fh:
                fh.write(actual_output)

            # if you use shlex.quote, it fails on Windows. why?
            command = " ".join(
                [
                    self.judge_command,  # already quoted and joined command
                    str(self.input_path.resolve()),
                    str(actual_output_path.resolve()),
                    str(
                        self.expected_output_path.resolve()
                        if self.expected_output_path is not None
                        else ""
                    ),
                ]
            )

            logger.debug("$ %s", command)
            info = measure_command(command)
        logger.debug("judge's output:\n%s", Printer(info.answer or ""))
        return info.returncode == 0


def build_match_function(
    *,
    error: float | None,
    judge_command: str | None,
    test_input_path: pathlib.Path,
    test_output_path: pathlib.Path | None,
) -> Callable[[bytes, bytes], bool]:
    """build_match_function builds the function to compare actual outputs and expected outputs.

    This function doesn't any I/O.
    """
    if judge_command is not None:
        return SpecialJudge(
            judge_command,
            input_path=test_input_path,
            expected_output_path=test_output_path,
        ).run

    is_exact = False
    if error is None:
        is_exact = True
        file_comparator = comparer.CRLFInsensitiveComparator(comparer.ExactComparator())
    else:
        word_comparator: comparer.OutputComparator = (
            comparer.FloatingPointNumberComparator(rel_tol=error, abs_tol=error)
        )
        file_comparator = comparer.SplitLinesComparator(
            comparer.SplitComparator(word_comparator)
        )
        file_comparator = comparer.CRLFInsensitiveComparator(file_comparator)

    def compare_outputs(actual: bytes, expected: bytes) -> bool:
        result = file_comparator(actual, expected)
        if not result and is_exact:
            non_stcict_comparator = comparer.CRLFInsensitiveComparator(
                comparer.SplitComparator(comparer.ExactComparator())
            )
            if non_stcict_comparator(actual, expected):
                logger.warning("This was AC if spaces and newlines were ignored.")
        return result

    return compare_outputs


def run_checking_output(
    *,
    answer: bytes,
    test_output_path: pathlib.Path | None,
    is_special_judge: bool,
    match_function: Callable[[bytes, bytes], bool],
) -> bool | None:
    """run_checking_output executes matching of the actual output and the expected output.

    This function has file I/O including the execution of the judge command.
    """
    if test_output_path is None and not is_special_judge:
        return None
    if test_output_path is not None:
        with test_output_path.open("rb") as outf:
            expected = outf.read()
    else:
        # only if --judge option
        expected = b""
        logger.warning("expected output is not found")
    return match_function(answer, expected)


def single_case(
    test_name: str,
    test_input_path: pathlib.Path,
    test_output_path: pathlib.Path | None,
    *,
    args: OjTestArguments,
) -> OjTestcaseResult:
    try:
        logger.info("%s", test_name)

        # run the binary
        with test_input_path.open("rb") as infp:
            info = measure_command(
                args.command,
                env=args.env,
                stdin=infp,
                timeout=args.tle,
                gnu_time=True,
            )
            answer = info.answer or b""
            elapsed: float = info.elapsed
            memory: float | None = info.memory

        if memory:
            logger.info("time: %f sec, memory: %f MB", elapsed, memory)
        else:
            logger.info("time: %f sec", elapsed)

        match_function = build_match_function(
            error=args.error,
            judge_command=str(args.judge) if args.judge else None,
            test_input_path=test_input_path,
            test_output_path=test_output_path,
        )
        match_result = run_checking_output(
            answer=answer,
            test_output_path=test_output_path,
            is_special_judge=args.judge is not None,
            match_function=match_function,
        )
        status = display_result(
            info.returncode,
            answer,
            memory,
            test_input_path,
            test_output_path,
            mle=args.mle,
            match_result=match_result,
        )

        # return the result
        return OjTestcaseResult(
            name=test_name,
            input=test_input_path,
            output=test_output_path,
            status=status,
            exitcode=info.returncode,
            elapsed=elapsed,
            memory=memory,
        )
    except _ExecError:
        return OjTestcaseResult(
            name=test_name,
            input=test_input_path,
            output=test_output_path,
            status=JudgeStatus.RE,
            exitcode=255,
            elapsed=0,
            memory=None,
        )


def _run(args: OjTestArguments) -> OjTestResult:
    # list tests
    test = fmtutils.glob_with_format(args.directory, "%s.%e")  # by default
    test = fmtutils.drop_backup_or_hidden_files(test)
    tests = fmtutils.construct_relationship_of_files(test, args.directory, "%s.%e")

    # check wheather GNU time is available
    if gnu.time_command() is None:
        if platform.system() == "Darwin":
            logger.info(
                "%s: You can install GNU time with: $ brew install gnu-time",
            )
        if args.mle is not None:
            raise RuntimeError("--mle is used but GNU time does not exist")

    # run tests
    history: list[OjTestcaseResult] = []
    for name, paths in sorted(tests.items()):
        if time.perf_counter() > args.deadline:
            raise VerifcationTimeoutError

        history.append(
            single_case(name, paths["in"], paths.get("out"), args=args),
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
            slowest_name = result.name
        if result.memory is not None and heaviest < result.memory:
            heaviest = result.memory
            heaviest_name = result.name

    # print the summary
    logger.info("slowest: %f sec  (for %s)", slowest, slowest_name)
    if heaviest >= 0:
        logger.info("max memory: %f MB  (for %s)", heaviest, heaviest_name)
    if ac_count == len(tests):
        logger.info(
            "%s: test %s: %d cases",
            SUCCESS,
            green("success"),
            len(tests),
        )
    else:
        logger.info(
            "%s: test %s: %d AC / %d cases",
            FAILURE,
            red("failed"),
            ac_count,
            len(tests),
        )

    # return the result
    return OjTestResult(
        is_success=ac_count == len(tests),
        slowest=slowest,
        elapsed=elapsed,
        heaviest=heaviest,
        testcases=history,
    )


def run_wrapper(
    *,
    problem: Problem,
    command: str | list[str],
    env: dict[str, str] | None,
    tle: float | None,
    mle: float | None,
    error: float | None,
    deadline: float = float("inf"),
) -> VerificationResult:
    directory = problem.problem_directory
    test_directory = directory / "test"

    args = OjTestArguments(
        command=command,
        env=env,
        directory=test_directory,
        tle=tle,
        mle=mle,
        error=error,
        judge=problem.checker,
        deadline=deadline,
    )
    result = _run(args)

    return VerificationResult(
        status=ResultStatus.SUCCESS if result.is_success else ResultStatus.FAILURE,
        elapsed=result.elapsed,
        slowest=result.slowest,
        heaviest=result.heaviest,
        testcases=[
            TestcaseResult(
                name=case.name,
                elapsed=case.elapsed,
                memory=case.memory,
                status=case.status,
            )
            for case in result.testcases
        ],
    )
