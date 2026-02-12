import logging
import pathlib
from typing import Any, NamedTuple

import pytest
from pytest_mock import MockerFixture

from competitive_verifier import oj
from competitive_verifier.models import JudgeStatus
from competitive_verifier.oj.oj_test import (
    OjExecInfo,
    OjTestArguments,
    OjTestcaseResult,
    Problem,
    SpecialJudge,
    single_case,
)
from competitive_verifier.oj.problem import (
    AOJProblem,
    LibraryCheckerProblem,
    YukicoderProblem,
)

OJ_TEST_MODULE = "competitive_verifier.oj.oj_test"


@pytest.fixture
def mock_measure(
    mocker: MockerFixture,
    request: pytest.FixtureRequest,
):
    assert isinstance(request.param, OjExecInfo)

    mocker.patch(
        "competitive_verifier.oj.oj_test.measure_command",
        return_value=request.param,
    )
    return request.param


@pytest.fixture
def mock_generate_test_cases(mocker: MockerFixture):
    mocker.patch.object(
        LibraryCheckerProblem,
        "generate_test_cases",
    )


@pytest.fixture
def mock_judge(
    mocker: MockerFixture,
    request: pytest.FixtureRequest,
) -> Problem:
    assert request.param is None or isinstance(request.param, bool)

    if request.param is not None:
        mocker.patch.object(SpecialJudge, "run", return_value=request.param)
        mocker.patch.object(
            LibraryCheckerProblem,
            "checker",
            return_value=pathlib.Path("/anywhere/mockcheck"),
            new_callable=mocker.PropertyMock,
        )
        return LibraryCheckerProblem(problem_id="aplusb")
    return AOJProblem(problem_id="1")


class SingleCaseParams(NamedTuple):
    name: str
    inbytes: bytes
    mock_measure: OjExecInfo
    expected: OjTestcaseResult
    expected_log: list[tuple[str, int, str]]
    outbytes: bytes | None = None
    error: float | None = None
    mle: float | None = None
    mock_judge: bool | None = None


def make_result(
    name: str,
    elapsed: float,
    exitcode: int | None,
    memory: float | None,
    status: JudgeStatus,
) -> OjTestcaseResult:
    return OjTestcaseResult(
        name=name,
        elapsed=elapsed,
        exitcode=exitcode,
        memory=memory,
        status=status,
        input=pathlib.Path(),
        answer=b"",
    )


def log_output(msg: str, *, module: str = OJ_TEST_MODULE, level: int = logging.INFO):
    return (module, level, msg)


test_single_case_params: list[SingleCaseParams] = [
    SingleCaseParams(
        name="default",
        inbytes=b"abc\n",
        outbytes=b"ABC\n",
        mock_measure=OjExecInfo(
            answer=b"ABC\n", elapsed=1.25, memory=None, returncode=0
        ),
        expected=make_result(
            name="default",
            elapsed=1.25,
            exitcode=0,
            memory=None,
            status=JudgeStatus.AC,
        ),
        expected_log=[
            log_output("default: start"),
            log_output("default: \x1b[32mAC\x1b[39m, time: 1.250000 sec"),
        ],
    ),
    SingleCaseParams(
        name="no_output",
        inbytes=b"abc\n",
        mock_measure=OjExecInfo(
            answer=b"ABC\n", elapsed=1.25, memory=None, returncode=0
        ),
        expected=make_result(
            name="no_output",
            elapsed=1.25,
            exitcode=0,
            memory=None,
            status=JudgeStatus.AC,
        ),
        expected_log=[
            log_output("no_output: start"),
            log_output("no_output:answer:\n\x1b[1mABC\x1b[0m\x1b[2m\\n\x1b[0m"),
            log_output("no_output: \x1b[32mAC\x1b[39m, time: 1.250000 sec"),
        ],
    ),
    SingleCaseParams(
        name="Nones",
        inbytes=b"",
        mock_measure=OjExecInfo(answer=None, elapsed=1.25, memory=None, returncode=0),
        expected=make_result(
            name="Nones",
            elapsed=1.25,
            exitcode=0,
            memory=None,
            status=JudgeStatus.AC,
        ),
        expected_log=[
            log_output("Nones: start"),
            log_output("Nones: \x1b[32mAC\x1b[39m, time: 1.250000 sec"),
        ],
    ),
    SingleCaseParams(
        name="memory",
        inbytes=b"",
        mock_measure=OjExecInfo(
            answer=b"19\n20", elapsed=1.25, memory=10.7, returncode=0
        ),
        expected=make_result(
            name="memory",
            elapsed=1.25,
            exitcode=0,
            memory=10.7,
            status=JudgeStatus.AC,
        ),
        expected_log=[
            log_output("memory: start"),
            log_output(
                msg="memory:answer:\n"
                "\x1b[1m19\x1b[0m\x1b[2m\\n\x1b[0m\x1b[1m20\x1b[0m\x1b[2m(no trailing newline)\x1b[0m",
            ),
            log_output(
                "memory: \x1b[32mAC\x1b[39m, time: 1.250000 sec, memory: 10.700000 MB"
            ),
        ],
    ),
    SingleCaseParams(
        name="spaces",
        inbytes=b"foo \t bar\nbaz \r\nhoge\nfuga\n",
        outbytes=b"1\n",
        mock_measure=OjExecInfo(answer=b"2\n", elapsed=1.25, memory=None, returncode=0),
        expected=make_result(
            name="spaces",
            elapsed=1.25,
            exitcode=0,
            memory=None,
            status=JudgeStatus.WA,
        ),
        expected_log=[
            log_output("spaces: start"),
            log_output(
                "spaces:input:\n"
                "\x1b[1mfoo\x1b[0m\x1b[2m_\\t_\x1b[0m\x1b[1mbar\x1b[0m\x1b[2m\\n"
                "\x1b[0m\x1b[1mbaz\x1b[0m\x1b[2m_\\r\x1b[0m\x1b[2m(trailing whitespace)\x1b[0m\x1b[2m\\n"
                "\x1b[0m\x1b[1mhoge\x1b[0m\x1b[2m\\n\x1b[0m\x1b[1mfuga\x1b[0m\x1b[2m\\n\x1b[0m",
            ),
            log_output("spaces:answer:\n\x1b[1m2\x1b[0m\x1b[2m\\n\x1b[0m"),
            log_output("spaces:expected:\n\x1b[1m1\x1b[0m\x1b[2m\\n\x1b[0m"),
            log_output("spaces: \x1b[31mWA\x1b[39m, time: 1.250000 sec"),
        ],
    ),
    SingleCaseParams(
        name="empty-lines",
        inbytes=b"\n\n\n\n",
        outbytes=b"1\n",
        mock_measure=OjExecInfo(answer=b"2\n", elapsed=1.25, memory=None, returncode=0),
        expected=make_result(
            name="empty-lines",
            elapsed=1.25,
            exitcode=0,
            memory=None,
            status=JudgeStatus.WA,
        ),
        expected_log=[
            log_output("empty-lines: start"),
            log_output("empty-lines:input:\n\x1b[2m\\n\\n\\n\\n\x1b[0m"),
            log_output("empty-lines:answer:\n\x1b[1m2\x1b[0m\x1b[2m\\n\x1b[0m"),
            log_output("empty-lines:expected:\n\x1b[1m1\x1b[0m\x1b[2m\\n\x1b[0m"),
            log_output("empty-lines: \x1b[31mWA\x1b[39m, time: 1.250000 sec"),
        ],
    ),
    SingleCaseParams(
        name="judge-AC",
        inbytes=b"abc\n",
        outbytes=b"ABC\n",
        mock_judge=True,
        mock_measure=OjExecInfo(
            answer=b"ABC\n", elapsed=1.25, memory=None, returncode=0
        ),
        expected=make_result(
            name="judge-AC",
            elapsed=1.25,
            exitcode=0,
            memory=None,
            status=JudgeStatus.AC,
        ),
        expected_log=[
            log_output("judge-AC: start"),
            log_output("judge-AC: \x1b[32mAC\x1b[39m, time: 1.250000 sec"),
        ],
    ),
    SingleCaseParams(
        name="judge-WA",
        inbytes=b"abc\n",
        outbytes=b"ABC\n",
        mock_judge=False,
        mock_measure=OjExecInfo(
            answer=b"ABC\n", elapsed=1.25, memory=None, returncode=0
        ),
        expected=make_result(
            name="judge-WA",
            elapsed=1.25,
            exitcode=0,
            memory=None,
            status=JudgeStatus.WA,
        ),
        expected_log=[
            log_output("judge-WA: start"),
            log_output("judge-WA:input:\n\x1b[1mabc\x1b[0m\x1b[2m\\n\x1b[0m"),
            log_output("judge-WA:answer:\n\x1b[1mABC\x1b[0m\x1b[2m\\n\x1b[0m"),
            log_output("judge-WA:expected:\n\x1b[1mABC\x1b[0m\x1b[2m\\n\x1b[0m"),
            log_output("judge-WA: \x1b[31mWA\x1b[39m, time: 1.250000 sec"),
        ],
    ),
    SingleCaseParams(
        name="judge-WA-no-expected-out",
        inbytes=b"abc\n",
        mock_judge=False,
        mock_measure=OjExecInfo(
            answer=b"ABC\n", elapsed=1.25, memory=None, returncode=0
        ),
        expected=make_result(
            name="judge-WA-no-expected-out",
            elapsed=1.25,
            exitcode=0,
            memory=None,
            status=JudgeStatus.WA,
        ),
        expected_log=[
            log_output("judge-WA-no-expected-out: start"),
            log_output("expected output is not found", level=logging.WARNING),
            log_output(
                "judge-WA-no-expected-out:input:\n\x1b[1mabc\x1b[0m\x1b[2m\\n\x1b[0m"
            ),
            log_output(
                "judge-WA-no-expected-out:answer:\n\x1b[1mABC\x1b[0m\x1b[2m\\n\x1b[0m"
            ),
            log_output("judge-WA-no-expected-out:expected:\n\x1b[2m(empty)\x1b[0m"),
            log_output(
                "judge-WA-no-expected-out: \x1b[31mWA\x1b[39m, time: 1.250000 sec"
            ),
        ],
    ),
    SingleCaseParams(
        name="check_output-WA",
        inbytes=b"abc\n",
        outbytes=b"ABC",
        mock_measure=OjExecInfo(
            answer=b"ABC\n", elapsed=1.25, memory=None, returncode=0
        ),
        expected=make_result(
            name="check_output-WA",
            elapsed=1.25,
            exitcode=0,
            memory=None,
            status=JudgeStatus.WA,
        ),
        expected_log=[
            log_output("check_output-WA: start"),
            log_output(
                "This was AC if spaces and newlines were ignored.",
                level=logging.WARNING,
            ),
            log_output(
                "check_output-WA:input:\n\x1b[1mabc\x1b[0m\x1b[2m\\n\x1b[0m",
            ),
            log_output("check_output-WA:answer:\n\x1b[1mABC\x1b[0m\x1b[2m\\n\x1b[0m"),
            log_output(
                "check_output-WA:expected:\n\x1b[1mABC\x1b[0m\x1b[2m(no trailing newline)\x1b[0m",
            ),
            log_output("check_output-WA: \x1b[31mWA\x1b[39m, time: 1.250000 sec"),
        ],
    ),
    SingleCaseParams(
        name="check_output-AC",
        inbytes=b"abc\n",
        outbytes=b"ABC\n",
        mock_measure=OjExecInfo(
            answer=b"ABC\n", elapsed=1.25, memory=None, returncode=0
        ),
        expected=make_result(
            name="check_output-AC",
            elapsed=1.25,
            exitcode=0,
            memory=None,
            status=JudgeStatus.AC,
        ),
        expected_log=[
            log_output("check_output-AC: start"),
            log_output("check_output-AC: \x1b[32mAC\x1b[39m, time: 1.250000 sec"),
        ],
    ),
    SingleCaseParams(
        name="error-AC-equals",
        inbytes=b"Pi\n",
        outbytes=b"3.14159265358\n",
        error=1e-11,
        mock_measure=OjExecInfo(
            answer=b"3.14159265358\n", elapsed=1.25, memory=None, returncode=0
        ),
        expected=make_result(
            name="error-AC-equals",
            elapsed=1.25,
            exitcode=0,
            memory=None,
            status=JudgeStatus.AC,
        ),
        expected_log=[
            log_output("error-AC-equals: start"),
            log_output("error-AC-equals: \x1b[32mAC\x1b[39m, time: 1.250000 sec"),
        ],
    ),
    SingleCaseParams(
        name="error-AC-long",
        inbytes=b"Pi\n",
        outbytes=b"3.141592653589793238462643383279502884197169399375105820974944592307816406286\n",
        error=1e-11,
        mock_measure=OjExecInfo(
            answer=b"3.14159265358\n", elapsed=1.25, memory=None, returncode=0
        ),
        expected=make_result(
            name="error-AC-long",
            elapsed=1.25,
            exitcode=0,
            memory=None,
            status=JudgeStatus.AC,
        ),
        expected_log=[
            log_output("error-AC-long: start"),
            log_output("error-AC-long: \x1b[32mAC\x1b[39m, time: 1.250000 sec"),
        ],
    ),
    SingleCaseParams(
        name="error-AC-short",
        inbytes=b"Pi\n",
        outbytes=b"3.1415926536\n",
        error=1e-11,
        mock_measure=OjExecInfo(
            answer=b"3.14159265358\n", elapsed=1.25, memory=None, returncode=0
        ),
        expected=make_result(
            name="error-AC-short",
            elapsed=1.25,
            exitcode=0,
            memory=None,
            status=JudgeStatus.AC,
        ),
        expected_log=[
            log_output("error-AC-short: start"),
            log_output("error-AC-short: \x1b[32mAC\x1b[39m, time: 1.250000 sec"),
        ],
    ),
    SingleCaseParams(
        name="error-small-AC-abs",
        inbytes=b"Planck mass\n",
        outbytes=b"0.0000000217640\n",
        error=1e-12,
        mock_measure=OjExecInfo(
            answer=b"0.0000000217647\n", elapsed=1.25, memory=None, returncode=0
        ),
        expected=make_result(
            name="error-small-AC-abs",
            elapsed=1.25,
            exitcode=0,
            memory=None,
            status=JudgeStatus.AC,
        ),
        expected_log=[
            log_output("error-small-AC-abs: start"),
            log_output("error-small-AC-abs: \x1b[32mAC\x1b[39m, time: 1.250000 sec"),
        ],
    ),
    SingleCaseParams(
        name="error-small-AC-abs-short",
        inbytes=b"Planck mass\n",
        outbytes=b"0.000000021764\n",
        error=1e-12,
        mock_measure=OjExecInfo(
            answer=b"0.0000000217647\n", elapsed=1.25, memory=None, returncode=0
        ),
        expected=make_result(
            name="error-small-AC-abs-short",
            elapsed=1.25,
            exitcode=0,
            memory=None,
            status=JudgeStatus.AC,
        ),
        expected_log=[
            log_output("error-small-AC-abs-short: start"),
            log_output(
                "error-small-AC-abs-short: \x1b[32mAC\x1b[39m, time: 1.250000 sec"
            ),
        ],
    ),
    SingleCaseParams(
        name="error-small-WA-abs",
        inbytes=b"Planck mass\n",
        outbytes=b"0.0000000217640\n",
        error=1e-13,
        mock_measure=OjExecInfo(
            answer=b"0.0000000217647\n", elapsed=1.25, memory=None, returncode=0
        ),
        expected=make_result(
            name="error-small-WA-abs",
            elapsed=1.25,
            exitcode=0,
            memory=None,
            status=JudgeStatus.WA,
        ),
        expected_log=[
            log_output("error-small-WA-abs: start"),
            log_output(
                "error-small-WA-abs:input:\n"
                "\x1b[1mPlanck\x1b[0m\x1b[2m_\x1b[0m\x1b[1mmass\x1b[0m\x1b[2m\\n\x1b[0m",
            ),
            log_output(
                "error-small-WA-abs:answer:\n\x1b[1m0.0000000217647\x1b[0m\x1b[2m\\n\x1b[0m",
            ),
            log_output(
                "error-small-WA-abs:expected:\n\x1b[1m0.0000000217640\x1b[0m\x1b[2m\\n\x1b[0m",
            ),
            log_output("error-small-WA-abs: \x1b[31mWA\x1b[39m, time: 1.250000 sec"),
        ],
    ),
    SingleCaseParams(
        name="error-large-AC-rel",
        inbytes=b"Planck temp\n",
        outbytes=b"141678400000000000000000000000000\n",
        error=1e-12,
        mock_measure=OjExecInfo(
            answer=b"141678400000000000000000000000000\n",
            elapsed=1.25,
            memory=None,
            returncode=0,
        ),
        expected=make_result(
            name="error-large-AC-rel",
            elapsed=1.25,
            exitcode=0,
            memory=None,
            status=JudgeStatus.AC,
        ),
        expected_log=[
            log_output("error-large-AC-rel: start"),
            log_output("error-large-AC-rel: \x1b[32mAC\x1b[39m, time: 1.250000 sec"),
        ],
    ),
    SingleCaseParams(
        name="error-large-AC-rel-diff",
        inbytes=b"Planck temp\n",
        outbytes=b"141678400000000000000000000000000\n",
        error=1e-12,
        mock_measure=OjExecInfo(
            answer=b"141678400000021987654321987654321\n",
            elapsed=1.25,
            memory=None,
            returncode=0,
        ),
        expected=make_result(
            name="error-large-AC-rel-diff",
            elapsed=1.25,
            exitcode=0,
            memory=None,
            status=JudgeStatus.AC,
        ),
        expected_log=[
            log_output("error-large-AC-rel-diff: start"),
            log_output(
                "error-large-AC-rel-diff: \x1b[32mAC\x1b[39m, time: 1.250000 sec"
            ),
        ],
    ),
    SingleCaseParams(
        name="error-large-WA-rel",
        inbytes=b"Planck temp\n",
        outbytes=b"141678400000000000000000000000000\n",
        error=1e-13,
        mock_measure=OjExecInfo(
            answer=b"141678400000021987654321987654321\n",
            elapsed=1.25,
            memory=None,
            returncode=0,
        ),
        expected=make_result(
            name="error-large-WA-rel",
            elapsed=1.25,
            exitcode=0,
            memory=None,
            status=JudgeStatus.WA,
        ),
        expected_log=[
            log_output("error-large-WA-rel: start"),
            log_output(
                "error-large-WA-rel:input:\n"
                "\x1b[1mPlanck\x1b[0m\x1b[2m_\x1b[0m\x1b[1mtemp\x1b[0m\x1b[2m\\n\x1b[0m",
            ),
            log_output(
                "error-large-WA-rel:answer:\n\x1b[1m141678400000021987654321987654321\x1b[0m\x1b[2m\\n\x1b[0m",
            ),
            log_output(
                "error-large-WA-rel:expected:\n\x1b[1m141678400000000000000000000000000\x1b[0m\x1b[2m\\n\x1b[0m",
            ),
            log_output("error-large-WA-rel: \x1b[31mWA\x1b[39m, time: 1.250000 sec"),
        ],
    ),
    SingleCaseParams(
        name="lines-same",
        inbytes=b"abc\n",
        outbytes=b"ABC\nDEF\nGH\n",
        mock_measure=OjExecInfo(
            answer=b"ABC\nDEF\nGH\n", elapsed=1.25, memory=None, returncode=0
        ),
        expected=make_result(
            name="lines-same",
            elapsed=1.25,
            exitcode=0,
            memory=None,
            status=JudgeStatus.AC,
        ),
        expected_log=[
            log_output("lines-same: start"),
            log_output("lines-same: \x1b[32mAC\x1b[39m, time: 1.250000 sec"),
        ],
    ),
    SingleCaseParams(
        name="lines-crlf",
        inbytes=b"abc\n",
        outbytes=b"ABC\nDEF\nGH\n",
        mock_measure=OjExecInfo(
            answer=b"ABC\r\nDEF\r\nGH\r\n", elapsed=1.25, memory=None, returncode=0
        ),
        expected=make_result(
            name="lines-crlf",
            elapsed=1.25,
            exitcode=0,
            memory=None,
            status=JudgeStatus.AC,
        ),
        expected_log=[
            log_output("lines-crlf: start"),
            log_output("lines-crlf: \x1b[32mAC\x1b[39m, time: 1.250000 sec"),
        ],
    ),
    SingleCaseParams(
        name="lines-diff",
        inbytes=b"abc\n",
        outbytes=b"ABC\nDEF\nGH\n",
        mock_measure=OjExecInfo(
            answer=b"ABC\nDDF\nGH\n", elapsed=1.25, memory=None, returncode=0
        ),
        expected=make_result(
            name="lines-diff",
            elapsed=1.25,
            exitcode=0,
            memory=None,
            status=JudgeStatus.WA,
        ),
        expected_log=[
            log_output("lines-diff: start"),
            log_output("lines-diff:input:\n\x1b[1mabc\x1b[0m\x1b[2m\\n\x1b[0m"),
            log_output(
                "lines-diff:answer:\n"
                "\x1b[1mABC\x1b[0m\x1b[2m\\n\x1b[0m\x1b[1mDDF\x1b[0m\x1b[2m\\n\x1b[0m\x1b[1mGH\x1b[0m\x1b[2m\\n\x1b[0m",
            ),
            log_output(
                "lines-diff:expected:\n"
                "\x1b[1mABC\x1b[0m\x1b[2m\\n\x1b[0m\x1b[1mDEF\x1b[0m\x1b[2m\\n\x1b[0m\x1b[1mGH\x1b[0m\x1b[2m\\n\x1b[0m",
            ),
            log_output("lines-diff: \x1b[31mWA\x1b[39m, time: 1.250000 sec"),
        ],
    ),
    SingleCaseParams(
        name="lines-error-diff-len",
        inbytes=b"abc\n",
        outbytes=b"ABC\nDEF\n3.14159265358979\n",
        error=1e-5,
        mock_measure=OjExecInfo(
            answer=b"ABC\nDEF\n3.14159265\n", elapsed=1.25, memory=None, returncode=0
        ),
        expected=make_result(
            name="lines-error-diff-len",
            elapsed=1.25,
            exitcode=0,
            memory=None,
            status=JudgeStatus.AC,
        ),
        expected_log=[
            log_output("lines-error-diff-len: start"),
            log_output("lines-error-diff-len: \x1b[32mAC\x1b[39m, time: 1.250000 sec"),
        ],
    ),
    SingleCaseParams(
        name="lines-error-grid",
        inbytes=b"abc\n",
        outbytes=b"ABC CD\nDEF 3.141592653589\n3.14159265358979\n",
        error=1e-5,
        mock_measure=OjExecInfo(
            answer=b"ABC CD\nDEF 3.14159265\n3.14159265\n",
            elapsed=1.25,
            memory=None,
            returncode=0,
        ),
        expected=make_result(
            name="lines-error-grid",
            elapsed=1.25,
            exitcode=0,
            memory=None,
            status=JudgeStatus.AC,
        ),
        expected_log=[
            log_output("lines-error-grid: start"),
            log_output("lines-error-grid: \x1b[32mAC\x1b[39m, time: 1.250000 sec"),
        ],
    ),
    SingleCaseParams(
        name="lines-grid-diff",
        inbytes=b"abc\n",
        outbytes=b"ABC CD\nDEF 3.141592653589\n3.14159265358979\n",
        error=1e-5,
        mock_measure=OjExecInfo(
            answer=b"ABC CD\nDEF 3.14159265 3.14\n3.14159265\n",
            elapsed=1.25,
            memory=None,
            returncode=0,
        ),
        expected=make_result(
            name="lines-grid-diff",
            elapsed=1.25,
            exitcode=0,
            memory=None,
            status=JudgeStatus.WA,
        ),
        expected_log=[
            log_output("lines-grid-diff: start"),
            log_output("lines-grid-diff:input:\n\x1b[1mabc\x1b[0m\x1b[2m\\n\x1b[0m"),
            log_output(
                "lines-grid-diff:answer:\n"
                "\x1b[1mABC\x1b[0m\x1b[2m_\x1b[0m\x1b[1mCD\x1b[0m\x1b[2m\\n"
                "\x1b[0m\x1b[1mDEF\x1b[0m\x1b[2m_\x1b[0m\x1b[1m3.14159265\x1b[0m\x1b[2m_\x1b[0m\x1b[1m3.14\x1b[0m\x1b[2m\\n"
                "\x1b[0m\x1b[1m3.14159265\x1b[0m\x1b[2m\\n\x1b[0m",
            ),
            log_output(
                "lines-grid-diff:expected:\n"
                "\x1b[1mABC\x1b[0m\x1b[2m_\x1b[0m\x1b[1mCD\x1b[0m\x1b[2m\\n"
                "\x1b[0m\x1b[1mDEF\x1b[0m\x1b[2m_\x1b[0m\x1b[1m3.141592653589\x1b[0m\x1b[2m\\n"
                "\x1b[0m\x1b[1m3.14159265358979\x1b[0m\x1b[2m\\n\x1b[0m",
            ),
            log_output("lines-grid-diff: \x1b[31mWA\x1b[39m, time: 1.250000 sec"),
        ],
    ),
    SingleCaseParams(
        name="lines-grid-diff-lines",
        inbytes=b"abc\n",
        outbytes=b"ABC CD\nDEF 3.141592653589\n3.14159265358979\n",
        error=1e-5,
        mock_measure=OjExecInfo(
            answer=b"ABC CD\nDEF 3.14159265 3.14\n3.14159265\nno\n",
            elapsed=1.25,
            memory=None,
            returncode=0,
        ),
        expected=make_result(
            name="lines-grid-diff-lines",
            elapsed=1.25,
            exitcode=0,
            memory=None,
            status=JudgeStatus.WA,
        ),
        expected_log=[
            log_output("lines-grid-diff-lines: start"),
            log_output(
                "lines-grid-diff-lines:input:\n\x1b[1mabc\x1b[0m\x1b[2m\\n\x1b[0m"
            ),
            log_output(
                "lines-grid-diff-lines:answer:\n"
                "\x1b[1mABC\x1b[0m\x1b[2m_\x1b[0m\x1b[1mCD\x1b[0m\x1b[2m\\n"
                "\x1b[0m\x1b[1mDEF\x1b[0m\x1b[2m_\x1b[0m\x1b[1m3.14159265\x1b[0m\x1b[2m_\x1b[0m\x1b[1m3.14\x1b[0m\x1b[2m\\n"
                "\x1b[0m\x1b[1m3.14159265\x1b[0m\x1b[2m\\n\x1b[0m\x1b[1mno\x1b[0m\x1b[2m\\n\x1b[0m",
            ),
            log_output(
                "lines-grid-diff-lines:expected:\n"
                "\x1b[1mABC\x1b[0m\x1b[2m_\x1b[0m\x1b[1mCD\x1b[0m\x1b[2m\\n"
                "\x1b[0m\x1b[1mDEF\x1b[0m\x1b[2m_\x1b[0m\x1b[1m3.141592653589\x1b[0m\x1b[2m\\n"
                "\x1b[0m\x1b[1m3.14159265358979\x1b[0m\x1b[2m\\n\x1b[0m",
            ),
            log_output("lines-grid-diff-lines: \x1b[31mWA\x1b[39m, time: 1.250000 sec"),
        ],
    ),
    SingleCaseParams(
        name="error-str-same",
        inbytes=b"abc\n",
        outbytes=b"ABC\n",
        error=1e-3,
        mock_measure=OjExecInfo(
            answer=b"ABC\n", elapsed=1.25, memory=None, returncode=0
        ),
        expected=make_result(
            name="error-str-same",
            elapsed=1.25,
            exitcode=0,
            memory=None,
            status=JudgeStatus.AC,
        ),
        expected_log=[
            log_output("error-str-same: start"),
            log_output("error-str-same: \x1b[32mAC\x1b[39m, time: 1.250000 sec"),
        ],
    ),
    SingleCaseParams(
        name="error-str-WA",
        inbytes=b"abc\n",
        outbytes=b"DEF\n",
        error=1e-3,
        mock_measure=OjExecInfo(
            answer=b"ABC\n", elapsed=1.25, memory=None, returncode=0
        ),
        expected=make_result(
            name="error-str-WA",
            elapsed=1.25,
            exitcode=0,
            memory=None,
            status=JudgeStatus.WA,
        ),
        expected_log=[
            log_output("error-str-WA: start"),
            log_output("error-str-WA:input:\n\x1b[1mabc\x1b[0m\x1b[2m\\n\x1b[0m"),
            log_output("error-str-WA:answer:\n\x1b[1mABC\x1b[0m\x1b[2m\\n\x1b[0m"),
            log_output("error-str-WA:expected:\n\x1b[1mDEF\x1b[0m\x1b[2m\\n\x1b[0m"),
            log_output("error-str-WA: \x1b[31mWA\x1b[39m, time: 1.250000 sec"),
        ],
    ),
    SingleCaseParams(
        name="TLE",
        inbytes=b"abc\n",
        outbytes=b"ABC\n",
        mock_measure=OjExecInfo(
            answer=b"ABC\n", elapsed=1.25, memory=None, returncode=None
        ),
        expected=make_result(
            name="TLE",
            elapsed=1.25,
            exitcode=None,
            memory=None,
            status=JudgeStatus.TLE,
        ),
        expected_log=[
            log_output("TLE: start"),
            log_output("TLE:input:\n\x1b[1mabc\x1b[0m\x1b[2m\\n\x1b[0m"),
            log_output("TLE:expected:\n\x1b[1mABC\x1b[0m\x1b[2m\\n\x1b[0m"),
            log_output("TLE: \x1b[31mTLE\x1b[39m, time: 1.250000 sec"),
        ],
    ),
    SingleCaseParams(
        name="RE",
        inbytes=b"abc\n",
        outbytes=b"ABC\n",
        mock_measure=OjExecInfo(
            answer=b"ABC\n", elapsed=1.25, memory=None, returncode=1
        ),
        expected=make_result(
            name="RE",
            elapsed=1.25,
            exitcode=1,
            memory=None,
            status=JudgeStatus.RE,
        ),
        expected_log=[
            log_output("RE: start"),
            log_output("RE:input:\n\x1b[1mabc\x1b[0m\x1b[2m\\n\x1b[0m"),
            log_output("RE:expected:\n\x1b[1mABC\x1b[0m\x1b[2m\\n\x1b[0m"),
            log_output("RE: \x1b[31mRE\x1b[39m, time: 1.250000 sec, return code: 1"),
        ],
    ),
    SingleCaseParams(
        name="MLE-NotMeasure",
        inbytes=b"abc\n",
        outbytes=b"ABC\n",
        mle=128,
        mock_measure=OjExecInfo(
            answer=b"ABC\n", elapsed=1.25, memory=None, returncode=0
        ),
        expected=make_result(
            name="MLE-NotMeasure",
            elapsed=1.25,
            exitcode=0,
            memory=None,
            status=JudgeStatus.AC,
        ),
        expected_log=[
            log_output("MLE-NotMeasure: start"),
            log_output("MLE-NotMeasure: \x1b[32mAC\x1b[39m, time: 1.250000 sec"),
        ],
    ),
    SingleCaseParams(
        name="MLE-Safe",
        inbytes=b"abc\n",
        outbytes=b"ABC\n",
        mle=128,
        mock_measure=OjExecInfo(
            answer=b"ABC\n", elapsed=1.25, memory=128, returncode=0
        ),
        expected=make_result(
            name="MLE-Safe",
            elapsed=1.25,
            exitcode=0,
            memory=128,
            status=JudgeStatus.AC,
        ),
        expected_log=[
            log_output("MLE-Safe: start"),
            log_output(
                "MLE-Safe: \x1b[32mAC\x1b[39m, time: 1.250000 sec, memory: 128.000000 MB"
            ),
        ],
    ),
    SingleCaseParams(
        name="MLE",
        inbytes=b"abc\n",
        outbytes=b"ABC\n",
        mle=128,
        mock_measure=OjExecInfo(
            answer=b"ABC\n", elapsed=1.25, memory=128.1, returncode=1
        ),
        expected=make_result(
            name="MLE",
            elapsed=1.25,
            exitcode=1,
            memory=128.1,
            status=JudgeStatus.MLE,
        ),
        expected_log=[
            log_output("MLE: start"),
            log_output("MLE:input:\n\x1b[1mabc\x1b[0m\x1b[2m\\n\x1b[0m"),
            log_output("MLE:answer:\n\x1b[1mABC\x1b[0m\x1b[2m\\n\x1b[0m"),
            log_output("MLE:expected:\n\x1b[1mABC\x1b[0m\x1b[2m\\n\x1b[0m"),
            log_output(
                "MLE: \x1b[31mMLE\x1b[39m,"
                " time: 1.250000 sec, memory: 128.100000 MB, return code: 1"
            ),
        ],
    ),
    SingleCaseParams(
        name="unicode-error",
        inbytes=b"a\n",
        outbytes=b"A\n",
        mock_measure=OjExecInfo(
            answer=b"\x82\xa0\n", elapsed=1.25, memory=None, returncode=0
        ),
        expected=make_result(
            name="unicode-error",
            elapsed=1.25,
            exitcode=0,
            memory=None,
            status=JudgeStatus.WA,
        ),
        expected_log=[
            log_output("unicode-error: start"),
            log_output("unicode-error:input:\n\x1b[1ma\x1b[0m\x1b[2m\\n\x1b[0m"),
            log_output(
                "unicode-error:answer:\n"
                "\x1b[2m'utf-8' codec can't decode byte 0x82 in position 0: invalid "
                "start byte\x1b[0m\x1b[1m\ufffd\ufffd\x1b[0m\x1b[2m\\n\x1b[0m"
            ),
            log_output("unicode-error:expected:\n\x1b[1mA\x1b[0m\x1b[2m\\n\x1b[0m"),
            log_output("unicode-error: \x1b[31mWA\x1b[39m, time: 1.250000 sec"),
        ],
    ),
    SingleCaseParams(
        name="long-lines",
        inbytes=b"abc\n",
        outbytes=b"ABC\n",
        mock_measure=OjExecInfo(
            answer=b"""ea226088-3cc7-4d33-985c-00004dfcdccb
6f791930-4b08-4618-a110-32be65332f08
87f28765-03bb-4aa3-ad2c-5e781aa60ca0
2c006877-aeae-4b24-88f1-29351ac40ad7
73380cec-9775-4b5d-9f86-b0bba61f2608
""",
            elapsed=1.25,
            memory=None,
            returncode=0,
        ),
        expected=make_result(
            name="long-lines",
            elapsed=1.25,
            exitcode=0,
            memory=None,
            status=JudgeStatus.WA,
        ),
        expected_log=[
            log_output("long-lines: start"),
            log_output("long-lines:input:\n\x1b[1mabc\x1b[0m\x1b[2m\\n\x1b[0m"),
            log_output(
                "long-lines:answer:\n"
                "\x1b[1mea226088-3cc7-4d33-9\x1b[0m\x1b[2m... (145 chars) "
                "...\x1b[0m\x1b[1md-9f86-b0bba61f2608\x1b[0m\x1b[2m\\n\x1b[0m",
            ),
            log_output("long-lines:expected:\n\x1b[1mABC\x1b[0m\x1b[2m\\n\x1b[0m"),
            log_output("long-lines: \x1b[31mWA\x1b[39m, time: 1.250000 sec"),
        ],
    ),
    SingleCaseParams(
        name="long-text",
        inbytes=b"abc\n",
        outbytes=b"ABC\n",
        mock_measure=OjExecInfo(
            answer=b"ea226088-3cc7-4d33-985c-00004dfcdccb6f791930-4b08-4618-a110-32be65332f08"
            b"87f28765-03bb-4aa3-ad2c-5e781aa60ca09b063b0f-7b48-4a1d-a49f-4e8524ace9174"
            b"2e6d61b-9656-4cb6-be7a-1a5d80224390961bed54-a32d-47c7-bb82-ae4591ed8ccd\r\n",
            elapsed=1.25,
            memory=None,
            returncode=0,
        ),
        expected=make_result(
            name="long-text",
            elapsed=1.25,
            exitcode=0,
            memory=None,
            status=JudgeStatus.WA,
        ),
        expected_log=[
            log_output("long-text: start"),
            log_output(
                "long-text:input:\n\x1b[1mabc\x1b[0m\x1b[2m\\n\x1b[0m",
            ),
            log_output(
                "long-text:answer:\n"
                "\x1b[1mea226088-3cc7-4d33-9\x1b[0m\x1b[2m... (178 chars) ...\x1b[0m"
                "\x1b[1m-bb82-ae4591ed8ccd\x1b[0m\x1b[2m\\r\\n\x1b[0m",
            ),
            log_output("long-text:expected:\n\x1b[1mABC\x1b[0m\x1b[2m\\n\x1b[0m"),
            log_output("long-text: \x1b[31mWA\x1b[39m, time: 1.250000 sec"),
        ],
    ),
    SingleCaseParams(
        name="long-lines-break",
        inbytes=b"abc\n",
        outbytes=b"ABC\n",
        mock_measure=OjExecInfo(
            answer=b"""ea226088-3cc7-4d33-\n985c-00004dfcdccb
6f791930-4b08-4618-a110-32be65332f08
87f28765-03bb-4aa3-ad2c-5e781aa60ca0
2c006877-aeae-4b24-88f1-29351ac40ad7
73380cec-9775-4b5d\n-9f86-b0bba61f2608
""",
            elapsed=1.25,
            memory=None,
            returncode=0,
        ),
        expected=make_result(
            name="long-lines-break",
            elapsed=1.25,
            exitcode=0,
            memory=None,
            status=JudgeStatus.WA,
        ),
        expected_log=[
            log_output("long-lines-break: start"),
            log_output("long-lines-break:input:\n\x1b[1mabc\x1b[0m\x1b[2m\\n\x1b[0m"),
            log_output(
                "long-lines-break:answer:\n"
                "\x1b[1mea226088-3cc7-4d33-\x1b[0m\x1b[2m\\n\x1b[0m\x1b[2m... (147 chars) "
                "...\x1b[0m\x1b[2m\\n\x1b[0m\x1b[1m-9f86-b0bba61f2608\x1b[0m\x1b[2m\\n\x1b[0m",
            ),
            log_output(
                "long-lines-break:expected:\n\x1b[1mABC\x1b[0m\x1b[2m\\n\x1b[0m"
            ),
            log_output("long-lines-break: \x1b[31mWA\x1b[39m, time: 1.250000 sec"),
        ],
    ),
]


@pytest.mark.usefixtures("mock_generate_test_cases")
@pytest.mark.parametrize(
    SingleCaseParams._fields,
    test_single_case_params,
    ids=[f"{i}:{t.name}" for i, t in enumerate(test_single_case_params)],
    indirect=["mock_measure", "mock_judge"],
)
def test_single_case(
    name: str,
    inbytes: bytes,
    outbytes: bytes | None,
    error: float | None,
    mle: float | None,
    expected: OjTestcaseResult,
    expected_log: list[tuple[str, int, str]],
    caplog: pytest.LogCaptureFixture,
    mock_judge: Problem,
    mock_measure: OjExecInfo,
    testtemp: pathlib.Path,
):
    caplog.set_level(logging.NOTSET)
    input_path = testtemp / "infile"
    input_path.write_bytes(inbytes)

    if outbytes is None:
        output_path = None
    else:
        output_path = testtemp / "outfile"
        output_path.write_bytes(outbytes)

    result = single_case(
        name,
        test_input_path=input_path,
        test_output_path=output_path,
        args=OjTestArguments(
            command="ls ~",
            problem=mock_judge,
            error=error,
            mle=mle,
            tle=None,
        ),
    )

    expected.answer = mock_measure.answer or b""
    expected.input = input_path
    expected.expected = output_path
    assert result == expected
    assert caplog.record_tuples == expected_log


test_oj_test_params: dict[str, tuple[dict[str, Any], OjTestArguments]] = {
    "default": (
        {
            "problem": LibraryCheckerProblem(problem_id="example"),
            "command": "ls .",
            "tle": 2,
            "error": None,
            "mle": 128,
            "env": None,
        },
        OjTestArguments(
            command="ls .",
            tle=2,
            mle=128,
            error=None,
            problem=LibraryCheckerProblem(problem_id="example"),
        ),
    ),
    "with_env": (
        {
            "problem": YukicoderProblem(problem_no=10),
            "command": ["ls", "."],
            "tle": 30,
            "error": None,
            "mle": 256,
            "env": {"TOKEN": "Dummy"},
        },
        OjTestArguments(
            command=["ls", "."],
            tle=30,
            mle=256,
            error=None,
            problem=YukicoderProblem(problem_no=10),
            env={"TOKEN": "Dummy"},
        ),
    ),
}


@pytest.mark.parametrize(
    ("args", "expected"),
    test_oj_test_params.values(),
    ids=test_oj_test_params.keys(),
)
def test_oj_test(
    mocker: MockerFixture,
    args: dict[str, Any],
    expected: OjTestArguments,
):
    mocker.patch(
        "competitive_verifier.oj.problem.LibraryCheckerProblem.checker_exe_name",
        "mockcheck",
    )
    run = mocker.patch("competitive_verifier.oj.oj_test._run")

    oj.test(**args)

    run.assert_called_once_with(expected)
