import contextlib
import math
import os
import pathlib
import platform
import shlex
import signal
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from logging import getLogger
from typing import BinaryIO

from competitive_verifier.models import (
    JudgeStatus,
    ResultStatus,
    TestCaseProvider,
    TestcaseResult,
    VerifcationTimeoutError,
    VerificationResult,
)

from . import gnu
from .format import Printer, StatusCounter, green, red

logger = getLogger(__name__)


class _ExecError(Exception):
    pass


@dataclass
class OjExecInfo:
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
            logger.exception("exec:No such file or directory: %s", command)
            raise _ExecError from e
        except PermissionError as e:
            logger.exception("exec:Permission denied: %s", command)
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


@dataclass
class OjTestArguments:
    """Parameters for oj-test command.

    Port of onlinejudge_command.subcommand.test.add_subparser.
    """

    command: str | list[str]
    problem: TestCaseProvider
    tle: float | None
    mle: float | None
    error: float | None
    env: dict[str, str] | None = None
    deadline: float = float("inf")


@dataclass
class OjTestcaseResult:
    name: str
    """A name of the test case."""
    input: pathlib.Path
    """A input of the test case."""
    answer: bytes
    """A output of the test case."""

    status: JudgeStatus
    elapsed: float
    exitcode: int | None

    memory: float | None = None
    expected: pathlib.Path | None = None
    """A expected output of the test case."""

    def __post_init__(self):
        if not isinstance(self.exitcode, int):
            self.exitcode = None

    def __str__(self) -> str:
        p = [
            f"{self.name}: {green('AC')}"
            if self.status == JudgeStatus.AC
            else f"{self.name}: {red(self.status.name)}",
            f"time: {self.elapsed:f} sec",
            f"memory: {self.memory:f} MB" if self.memory is not None else None,
            f"return code: {self.exitcode}" if self.exitcode else None,
        ]

        return ", ".join(filter(None, p))

    def log(self):
        match self.status:
            case JudgeStatus.AC:
                if self.expected is None and self.answer:
                    self._log_answer()
            case JudgeStatus.RE | JudgeStatus.TLE:
                self._log_input()
                self._log_expected()
            case _:
                self._log_input()
                self._log_answer()
                self._log_expected()
        logger.info(self)

    def _log_input(self) -> None:
        with self.input.open("rb") as fp:
            logger.info("%s:input:\n%s", self.name, Printer(fp))

    def _log_expected(self) -> None:
        if self.expected:
            with self.expected.open("rb") as fp:
                logger.info("%s:expected:\n%s", self.name, Printer(fp))
        else:
            logger.info("%s:expected:\n%s", self.name, Printer(""))

    def _log_answer(self) -> None:
        logger.info("%s:answer:\n%s", self.name, Printer(self.answer))


@dataclass
class OjTestResult:
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


def _try_parse_float(value: bytes) -> float | None:
    try:
        return float(value)
    except ValueError:
        return None


def _equal_or_closed_float(actual: bytes, expected: bytes, *, error: float) -> bool:
    if actual == expected:
        return True

    x = _try_parse_float(actual)
    y = _try_parse_float(expected)

    return (
        x is not None
        and y is not None
        and math.isclose(x, y, rel_tol=error, abs_tol=error)
    )


def compare_answer(actual: bytes, expected: bytes, *, error: float | None) -> bool:
    """Compare two byte strings.

    Args:
        actual (bytes): Actual output
        expected (bytes): Expected output
        error (float | None): Margin of error
    Returns:
        bool: True if they are considered equal
    """
    if error is not None and error > 1:
        logger.warning("the tolerance is too large: relative = %s", error)

    actual = actual.replace(b"\r\n", b"\n")
    expected = expected.replace(b"\r\n", b"\n")

    # match
    if actual == expected:
        return True

    if error is None:
        actual_words = actual.split()
        expected_words = expected.split()
        if len(actual_words) == len(expected_words) and all(
            x == y for x, y in zip(actual_words, expected_words, strict=False)
        ):
            logger.warning("This was AC if spaces and newlines were ignored.")
        return False

    actual_lines = actual.rstrip(b"\n").split(b"\n")
    expected_lines = expected.rstrip(b"\n").split(b"\n")

    if len(actual_lines) != len(expected_lines):
        return False

    for actual_line, expected_line in zip(actual_lines, expected_lines, strict=False):
        actual_words = actual_line.split()
        expected_words = expected_line.split()

        if len(actual_words) != len(expected_words):
            return False

        for x, y in zip(actual_words, expected_words, strict=False):
            if not _equal_or_closed_float(x, y, error=error):
                return False
    return True


def check_output(
    *,
    answer: bytes,
    error: float | None,
    test_input_path: pathlib.Path,
    test_output_path: pathlib.Path | None,
    judge_command: str | None,
) -> bool | None:
    if test_output_path is None and not judge_command:
        return None
    if test_output_path is not None:
        with test_output_path.open("rb") as outf:
            expected = outf.read()
    else:
        # only if --judge option
        expected = b""
        logger.warning("expected output is not found")
    if judge_command is not None:
        return SpecialJudge(
            judge_command,
            input_path=test_input_path,
            expected_output_path=test_output_path,
        ).run(answer, expected)

    return compare_answer(answer, expected, error=error)


def determine_status(
    *,
    exitcode: int | None,
    memory: float | None,
    mle: float | None,
    match_result: bool | None,
) -> JudgeStatus:
    if exitcode is None:
        return JudgeStatus.TLE
    if memory is not None and mle is not None and memory > mle:
        return JudgeStatus.MLE
    if exitcode != 0:
        return JudgeStatus.RE
    if match_result is not None and not match_result:
        return JudgeStatus.WA
    return JudgeStatus.AC


def single_case(
    test_name: str,
    test_input_path: pathlib.Path,
    test_output_path: pathlib.Path | None,
    *,
    args: OjTestArguments,
) -> OjTestcaseResult:
    try:
        logger.info("%s: start", test_name)

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

        match_result = check_output(
            answer=answer,
            error=args.error,
            test_input_path=test_input_path,
            test_output_path=test_output_path,
            judge_command=str(args.problem.checker) if args.problem.checker else None,
        )
        status = determine_status(
            exitcode=info.returncode,
            memory=memory,
            mle=args.mle,
            match_result=match_result,
        )

        result = OjTestcaseResult(
            name=test_name,
            input=test_input_path,
            expected=test_output_path,
            answer=answer,
            status=status,
            exitcode=info.returncode,
            elapsed=elapsed,
            memory=memory,
        )
    except _ExecError:
        return OjTestcaseResult(
            name=test_name,
            input=test_input_path,
            expected=test_output_path,
            answer=b"",
            status=JudgeStatus.RE,
            exitcode=255,
            elapsed=0,
            memory=None,
        )
    else:
        result.log()
        return result


def _run(args: OjTestArguments) -> OjTestResult:
    # check wheather GNU time is available
    if gnu.time_command() is None:
        if platform.system() == "Darwin":
            logger.info(
                "%s: You can install GNU time with: $ brew install gnu-time",
            )
        if args.mle is not None:
            raise RuntimeError("--mle is used but GNU time does not exist")

    tests = list(args.problem.iter_system_cases())

    # run tests
    history: list[OjTestcaseResult] = []
    for t in tests:
        if time.perf_counter() > args.deadline:
            raise VerifcationTimeoutError

        history.append(single_case(t.name, t.input_path, t.output_path, args=args))

    # summarize
    elapsed: float = 0.0
    slowest: float = -1.0
    slowest_name = ""
    heaviest: float = -1.0
    heaviest_name = ""
    counter = StatusCounter()
    for result in history:
        counter[result.status] += 1
        elapsed += result.elapsed
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

    is_success = counter[JudgeStatus.AC] == len(tests)
    if is_success:
        logger.info("%s %d cases", green("SUCCESS"), len(tests))
    else:
        logger.info("%s %s / %d cases", red("FAILURE"), counter, len(tests))

    # return the result
    return OjTestResult(
        is_success=is_success,
        slowest=slowest,
        elapsed=elapsed,
        heaviest=heaviest,
        testcases=history,
    )


def main(
    *,
    problem: TestCaseProvider,
    command: str | list[str],
    env: dict[str, str] | None,
    tle: float | None,
    mle: float | None,
    error: float | None,
    deadline: float = float("inf"),
) -> VerificationResult:
    args = OjTestArguments(
        command=command,
        problem=problem,
        env=env,
        tle=tle,
        mle=mle,
        error=error,
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
