import contextlib
import json
import os
import pathlib
import platform
import shlex
import signal
import subprocess
import sys
import tempfile
import threading
import time
import traceback
from logging import getLogger
from subprocess import PIPE, Popen, TimeoutExpired
from typing import Annotated, Any, BinaryIO, Callable, Optional, Union

import onlinejudge._implementation.format_utils as fmtutils
from pydantic import BaseModel, Field
from pydantic.functional_validators import BeforeValidator

from competitive_verifier.models import (
    JudgeStatus,
    ResultStatus,
    TestcaseResult,
    VerificationResult,
)

from . import output_comparators, pretty_printers, utils
from .func import checker_exe_name, get_cache_directory, get_directory

logger = getLogger(__name__)


class OjTestArguments(BaseModel):
    """onlinejudge_command.subcommand.test.add_subparser"""

    command: Union[str, list[str]]
    cookie: pathlib.Path
    env: Optional[dict[str, str]] = None
    directory: pathlib.Path
    judge: Optional[pathlib.Path]
    tle: Optional[float]
    mle: Optional[float]
    error: Optional[float]
    print_input: bool = True
    format: str = "%s.%e"
    test: list[pathlib.Path] = Field(default_factory=list)
    gnu_time: Optional[str] = None
    log_file: Optional[pathlib.Path] = None
    silent: bool = False
    ignore_backup: bool = True


class OjExecInfo(BaseModel):
    answer: Optional[bytes]
    elapsed: float
    memory: Optional[float]


def oj_exec_command(
    command: Union[str, list[str]],
    *,
    env: Optional[dict[str, str]],
    stdin: Optional[BinaryIO] = None,
    input: Optional[bytes] = None,
    timeout: Optional[float] = None,
    gnu_time: Optional[str] = None,
) -> tuple[OjExecInfo, Popen[bytes]]:
    if input is not None:
        assert stdin is None
        stdin = PIPE  # type: ignore
    if gnu_time is not None:
        context: Any = tempfile.NamedTemporaryFile(delete=True)
    else:
        context = contextlib.nullcontext()
    with context as fh:
        if isinstance(command, str):
            command_str = command
            command = shlex.split(command)
            if gnu_time is not None:
                command = [gnu_time, "-f", "%M", "-o", fh.name, "--"] + command
            if sys.platform == "win32":
                # HACK: without this encoding and decoding, something randomly fails with multithreading; see https://github.com/kmyk/online-judge-tools/issues/468
                command = command_str.encode().decode()  # type: ignore
        begin = time.perf_counter()

        # We need kill processes called from the "time" command using process groups. Without this, orphans spawn. see https://github.com/kmyk/online-judge-tools/issues/640
        preexec_fn = None
        if gnu_time is not None and os.name == "posix":
            preexec_fn = os.setsid

        try:
            if env:
                env = os.environ | env
            proc = Popen(
                command,
                env=env,
                stdin=stdin,
                stdout=PIPE,
                stderr=sys.stderr,
                preexec_fn=preexec_fn,
            )  # pylint: disable=subprocess-popen-preexec-fn
        except FileNotFoundError:
            logger.error("No such file or directory: %s", command)
            sys.exit(1)
        except PermissionError:
            logger.error("Permission denied: %s", command)
            sys.exit(1)
        answer: Optional[bytes] = None
        try:
            answer, _ = proc.communicate(input=input, timeout=timeout)
        except TimeoutExpired:
            pass
        finally:
            if preexec_fn is not None:
                try:
                    if sys.platform != "win32":
                        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
                except ProcessLookupError:
                    pass
            else:
                proc.terminate()

        end = time.perf_counter()
        memory: Optional[float] = None
        if gnu_time is not None:
            with open(fh.name) as fh1:
                reported = fh1.read()
            logger.debug("GNU time says:\n%s", reported)
            if reported.strip() and reported.splitlines()[-1].isdigit():
                memory = int(reported.splitlines()[-1]) / 1000
    return (
        OjExecInfo(
            answer=answer,
            memory=memory,
            elapsed=end - begin,
        ),
        proc,
    )


# flake8: noqa: C901
def display_result(
    proc: Popen[bytes],
    answer: str,
    memory: Optional[float],
    test_input_path: pathlib.Path,
    test_output_path: Optional[pathlib.Path],
    *,
    mle: Optional[float],
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
                    "input:\n%s",
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
            logger.info(
                "output:\n%s",
                pretty_printers.make_pretty_large_file_content(
                    answer.encode(), limit=40, head=20, tail=10
                ),
            )
            logger.info(
                "expected:\n%s",
                pretty_printers.make_pretty_large_file_content(
                    expected.encode(), limit=40, head=20, tail=10
                ),
            )
    if match_result is None:
        if not silent:
            print_input()
            logger.info(
                "output:\n%s",
                pretty_printers.make_pretty_large_file_content(
                    answer.encode(), limit=40, head=20, tail=10
                ),
            )
    if status == JudgeStatus.AC:
        logger.info(utils.SUCCESS + "" + utils.green("AC"))

    return status


class TestCase(BaseModel):
    name: str
    input: pathlib.Path
    output: Optional[pathlib.Path] = None


class OjTestcaseResult(BaseModel):
    status: JudgeStatus
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
    if not gnu_time:
        gnu_time = get_gnu_time_command()
    try:
        with tempfile.NamedTemporaryFile(delete=True) as fh:
            subprocess.check_call(
                [gnu_time, "-f", "%M KB", "-o", fh.name, "--", "true"]
            )
            with open(fh.name) as fh1:
                data = fh1.read()
            int(utils.remove_suffix(data.rstrip().splitlines()[-1], " KB"))
            return True
    except NameError:
        raise  # NameError is not a runtime error caused by the environment, but a coding mistake
    except AttributeError:
        raise  # AttributeError is also a mistake
    except Exception:
        logger.debug(traceback.format_exc())
    return False


class SpecialJudge:
    def __init__(self, judge_command: str, *, is_silent: bool):
        self.judge_command = judge_command  # already quoted and joined command
        self.is_silent = is_silent

    def run(
        self,
        *,
        actual_output: bytes,
        input_path: pathlib.Path,
        expected_output_path: Optional[pathlib.Path],
    ) -> bool:
        with tempfile.TemporaryDirectory() as tempdir:
            actual_output_path = pathlib.Path(tempdir) / "actual.out"
            with open(actual_output_path, "wb") as fh:
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
            info, proc = utils.exec_command(command)
        logger.debug(
            "judge's output:\n%s",
            pretty_printers.make_pretty_large_file_content(
                info["answer"] or b"", limit=40, head=20, tail=10
            ),
        )
        return proc.returncode == 0


def build_match_function(
    *,
    error: Optional[float],
    judge_command: Optional[str],
    silent: bool,
    test_input_path: pathlib.Path,
    test_output_path: Optional[pathlib.Path],
) -> Callable[[bytes, bytes], bool]:
    """build_match_function builds the function to compare actual outputs and expected outputs.

    This function doesn't any I/O.
    """

    if judge_command is not None:
        special_judge = SpecialJudge(judge_command=judge_command, is_silent=silent)

        def run_judge_command(actual: bytes, expected: bytes) -> bool:
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
    test_output_path: Optional[pathlib.Path],
    is_special_judge: bool,
    match_function: Callable[[bytes, bytes], bool],
) -> Optional[bool]:
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
    test_output_path: Optional[pathlib.Path],
    *,
    lock: Optional[threading.Lock] = None,
    args: OjTestArguments,
) -> dict[str, Any]:
    # print the header earlier if not in parallel
    if lock is None:
        logger.info("%s", test_name)

    # run the binary
    with test_input_path.open("rb") as inf:
        info, proc = oj_exec_command(
            args.command,
            env=args.env,
            stdin=inf,
            timeout=args.tle,
            gnu_time=args.gnu_time,
        )
        # TODO: the `answer` should be bytes, not str
        answer: str = (info.answer or b"").decode(errors="replace")
        elapsed: float = info.elapsed
        memory: Optional[float] = info.memory

    # lock is require to avoid mixing logs if in parallel
    with lock or contextlib.nullcontext():
        if lock is not None:
            logger.info("%s", test_name)
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
            answer=answer.encode(),
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
    testcase = {
        "name": test_name,
        "input": str(test_input_path.resolve()),
    }
    if test_output_path:
        testcase["output"] = str(test_output_path.resolve())
    return {
        "status": status.value,
        "testcase": testcase,
        "output": answer,
        "exitcode": proc.returncode,
        "elapsed": elapsed,
        "memory": memory,
    }


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


def run_wrapper(
    *,
    url: str,
    command: Union[str, list[str]],
    env: Optional[dict[str, str]],
    tle: Optional[float],
    mle: Optional[float],
    error: Optional[float],
) -> VerificationResult:
    directory = get_directory(url)
    test_directory = directory / "test"

    checker_path: Optional[pathlib.Path] = directory / checker_exe_name
    if not checker_path.exists():
        checker_path = None

    args = OjTestArguments(
        command=command,
        env=env,
        cookie=get_cache_directory() / "cookie.txt",
        directory=test_directory,
        tle=tle,
        mle=mle,
        error=error,
        print_input=True,
        judge=checker_path,
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
