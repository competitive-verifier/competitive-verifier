import pathlib
import platform
import tempfile
import time
from collections.abc import Callable
from logging import getLogger
from subprocess import Popen
from typing import Annotated

from pydantic import BaseModel, Field
from pydantic.functional_validators import BeforeValidator

from competitive_verifier.models import (
    JudgeStatus,
    ResultStatus,
    TestcaseResult,
    VerifcationTimeoutError,
    VerificationResult,
)

from . import gnu, output_comparators, pretty_printers, utils
from .func import checker_exe_name, problem_directory
from .service import format_utils as fmtutils

logger = getLogger(__name__)


class OjTestArguments(BaseModel):
    """Parameters for oj-test command.

    Port of onlinejudge_command.subcommand.test.add_subparser.
    """

    command: str | list[str]
    env: dict[str, str] | None = None
    directory: pathlib.Path
    judge: pathlib.Path | None
    tle: float | None
    mle: float | None
    error: float | None
    print_input: bool = True
    format: str = "%s.%e"
    test: list[pathlib.Path] = Field(default_factory=list[pathlib.Path])
    silent: bool = False
    ignore_backup: bool = True
    deadline: float = float("inf")


def display_result(
    proc: Popen[bytes],
    answer: bytes,
    memory: float | None,
    test_input_path: pathlib.Path,
    test_output_path: pathlib.Path | None,
    *,
    mle: float | None,
    does_print_input: bool,
    silent: bool,
    match_result: bool | None,
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
                    "input:\n%s",
                    pretty_printers.make_pretty_large_file_content(
                        inf.read(), limit=40, head=20, tail=10
                    ),
                )

    # check TLE, RE or not
    status = JudgeStatus.AC
    if proc.returncode is None:
        logger.info("%s%s", utils.FAILURE, utils.red("TLE"))
        status = JudgeStatus.TLE
        if not silent:
            print_input()
    elif memory is not None and mle is not None and memory > mle:
        logger.info("%s%s", utils.FAILURE, utils.red("MLE"))
        status = JudgeStatus.MLE
        if not silent:
            print_input()
    elif proc.returncode != 0:
        logger.info(
            "%s%s: return code %d", utils.FAILURE, utils.red("RE"), proc.returncode
        )
        status = JudgeStatus.RE
        if not silent:
            print_input()

    # check WA or not
    # 元の実装では TLE や RE でもこっちに来てしまうので elif に変更
    elif match_result is not None and not match_result:
        if status == JudgeStatus.AC:
            logger.info("%s%s", utils.FAILURE, utils.red("WA"))
        status = JudgeStatus.WA
        if not silent:
            print_input()
            if test_output_path is not None:
                with test_output_path.open("rb") as outf:
                    expected = outf.read().decode()
            else:
                expected = ""
            logger.info(
                "output:\n%s",
                pretty_printers.make_pretty_large_file_content(
                    answer, limit=40, head=20, tail=10
                ),
            )
            logger.info(
                "expected:\n%s",
                pretty_printers.make_pretty_large_file_content(
                    expected.encode(), limit=40, head=20, tail=10
                ),
            )
    if match_result is None and not silent:
        print_input()
        logger.info(
            "output:\n%s",
            pretty_printers.make_pretty_large_file_content(
                answer, limit=40, head=20, tail=10
            ),
        )
    if status == JudgeStatus.AC:
        logger.info("%s%s", utils.SUCCESS, utils.green("AC"))

    return status


class TestCase(BaseModel):
    name: str
    input: pathlib.Path
    output: pathlib.Path | None = None


class OjTestcaseResult(BaseModel):
    status: JudgeStatus
    elapsed: float
    memory: float | None = None
    exitcode: Annotated[
        int | None, BeforeValidator(lambda v: v if isinstance(v, int) else None)
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


class SpecialJudge:
    def __init__(self, judge_command: str, *, is_silent: bool):
        self.judge_command = judge_command  # already quoted and joined command
        self.is_silent = is_silent

    def run(
        self,
        *,
        actual_output: bytes,
        input_path: pathlib.Path,
        expected_output_path: pathlib.Path | None,
    ) -> bool:
        with tempfile.TemporaryDirectory() as tempdir:
            actual_output_path = pathlib.Path(tempdir) / "actual.out"
            with actual_output_path.open("wb") as fh:
                fh.write(actual_output)

            # if you use shlex.quote, it fails on Windows. why?
            command = " ".join(
                [
                    self.judge_command,  # already quoted and joined command
                    str(input_path.resolve()),
                    str(actual_output_path.resolve()),
                    str(
                        expected_output_path.resolve()
                        if expected_output_path is not None
                        else ""
                    ),
                ]
            )

            logger.debug("$ %s", command)
            info, proc = utils.measure_command(command)
        logger.debug(
            "judge's output:\n%s",
            pretty_printers.make_pretty_large_file_content(
                info.answer or b"", limit=40, head=20, tail=10
            ),
        )
        return proc.returncode == 0


def build_match_function(
    *,
    error: float | None,
    judge_command: str | None,
    silent: bool,
    test_input_path: pathlib.Path,
    test_output_path: pathlib.Path | None,
) -> Callable[[bytes, bytes], bool]:
    """build_match_function builds the function to compare actual outputs and expected outputs.

    This function doesn't any I/O.
    """
    if judge_command is not None:
        special_judge = SpecialJudge(judge_command=judge_command, is_silent=silent)

        def run_judge_command(actual: bytes, _: bytes) -> bool:
            # the second argument is ignored
            return special_judge.run(
                actual_output=actual,
                input_path=test_input_path,
                expected_output_path=test_output_path,
            )

        return run_judge_command

    is_exact = False
    if error is None:
        is_exact = True
        file_comparator = output_comparators.CRLFInsensitiveComparator(
            output_comparators.ExactComparator()
        )
    else:
        word_comparator: output_comparators.OutputComparator = (
            output_comparators.FloatingPointNumberComparator(
                rel_tol=error, abs_tol=error
            )
        )
        file_comparator = output_comparators.SplitLinesComparator(
            output_comparators.SplitComparator(word_comparator)
        )
        file_comparator = output_comparators.CRLFInsensitiveComparator(file_comparator)

    def compare_outputs(actual: bytes, expected: bytes) -> bool:
        result = file_comparator(actual, expected)
        if not result and is_exact:
            non_stcict_comparator = output_comparators.CRLFInsensitiveComparator(
                output_comparators.SplitComparator(output_comparators.ExactComparator())
            )
            if non_stcict_comparator(actual, expected):
                logger.warning(
                    "This was AC if spaces and newlines were ignored. Please use --ignore-spaces (-S) option or --ignore-spaces-and-newline (-N) option."
                )
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


def test_single_case(
    test_name: str,
    test_input_path: pathlib.Path,
    test_output_path: pathlib.Path | None,
    *,
    args: OjTestArguments,
) -> OjTestcaseResult:
    logger.info("%s", test_name)

    # run the binary
    with test_input_path.open("rb") as inf:
        info, proc = utils.measure_command(
            args.command,
            env=args.env,
            stdin=inf,
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
        silent=args.silent,
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
        proc,
        answer,
        memory,
        test_input_path,
        test_output_path,
        mle=args.mle,
        does_print_input=args.print_input,
        silent=args.silent,
        match_result=match_result,
    )

    # return the result
    return OjTestcaseResult(
        status=status,
        testcase=TestCase(
            name=test_name,
            input=test_input_path.resolve(),
            output=test_output_path,
        ),
        exitcode=proc.returncode,
        elapsed=elapsed,
        memory=memory,
    )


def run(args: OjTestArguments) -> OjTestResult:
    # list tests
    if not args.test:
        args.test = fmtutils.glob_with_format(args.directory, args.format)  # by default
    if args.ignore_backup:
        args.test = fmtutils.drop_backup_or_hidden_files(args.test)
    tests = fmtutils.construct_relationship_of_files(
        args.test, args.directory, args.format
    )

    # check wheather GNU time is available
    if gnu.time_command() is None:
        if platform.system() == "Darwin":
            logger.info(
                "%sYou can install GNU time with: $ brew install gnu-time", utils.HINT
            )
        if args.mle is not None:
            raise RuntimeError("--mle is used but GNU time does not exist")

    # run tests
    history: list[OjTestcaseResult] = []
    for name, paths in sorted(tests.items()):
        if time.perf_counter() > args.deadline:
            raise VerifcationTimeoutError

        history.append(
            test_single_case(name, paths["in"], paths.get("out"), args=args),
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
    logger.info("slowest: %f sec  (for %s)", slowest, slowest_name)
    if heaviest >= 0:
        logger.info("max memory: %f MB  (for %s)", heaviest, heaviest_name)
    if ac_count == len(tests):
        logger.info(
            "%stest %s: %d cases",
            utils.SUCCESS,
            utils.green("success"),
            len(tests),
        )
    else:
        logger.info(
            "%stest %s: %d AC / %d cases",
            utils.FAILURE,
            utils.red("failed"),
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
    url: str,
    command: str | list[str],
    env: dict[str, str] | None,
    tle: float | None,
    mle: float | None,
    error: float | None,
    deadline: float = float("inf"),
) -> VerificationResult:
    directory = problem_directory(url)
    test_directory = directory / "test"

    checker_path: pathlib.Path | None = directory / checker_exe_name
    if not checker_path.exists():
        checker_path = None

    args = OjTestArguments(
        command=command,
        env=env,
        directory=test_directory,
        tle=tle,
        mle=mle,
        error=error,
        print_input=True,
        judge=checker_path,
        deadline=deadline,
    )
    result = run(args)

    return VerificationResult(
        status=ResultStatus.SUCCESS if result.is_success else ResultStatus.FAILURE,
        elapsed=result.elapsed,
        slowest=result.slowest,
        heaviest=result.heaviest,
        testcases=[
            TestcaseResult(
                name=case.testcase.name,
                elapsed=case.elapsed,
                memory=case.memory,
                status=case.status,
            )
            for case in result.testcases
        ],
    )
