import logging
import pathlib
from itertools import chain
from typing import Any, NamedTuple, cast

import pytest
from pytest_mock import MockerFixture, MockType

from competitive_verifier import oj
from competitive_verifier.log import GitHubMessageParams
from competitive_verifier.models import (
    JudgeStatus,
    Problem,
    VerifcationTimeoutError,
)
from competitive_verifier.models import (
    TestCaseFile as SystemTestCaseFile,
)
from competitive_verifier.models import (
    TestCaseProvider as SystemTestCaseProvider,
)
from competitive_verifier.oj.oj_test import (
    OjExecInfo,
    OjTestArguments,
    OjTestcaseResult,
    OjTestResult,
    gnu_time_message,
    single_case,
    special_judge,
    summarize,
)
from competitive_verifier.oj.problem import (
    AOJProblem,
    LibraryCheckerProblem,
    YukicoderProblem,
)
from tests import LogComparer

OJ_TEST_MODULE = "competitive_verifier.oj.oj_test"


def make_result(
    name: str,
    status: JudgeStatus,
    elapsed: float = 1.25,
    memory: float | None = None,
    exitcode: int | None = 0,
) -> OjTestcaseResult:
    return OjTestcaseResult(
        name=name,
        elapsed=elapsed,
        exitcode=exitcode,
        memory=memory,
        status=status,
        input=pathlib.Path(),
        expected=pathlib.Path(),
        answer="",
    )


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
    judge = getattr(request, "param", None)

    if judge is not None:
        assert isinstance(judge, bool)
        mocker.patch(
            "competitive_verifier.oj.oj_test.special_judge",
            return_value=judge,
        )
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
    expected_log: list[LogComparer]
    outbytes: bytes
    error: float | None = None
    mle: float | None = None
    mock_judge: bool | None = None


test_single_case_params: list[SingleCaseParams] = [
    SingleCaseParams(
        name="default",
        inbytes=b"abc\n",
        outbytes=b"ABC\n",
        mock_measure=OjExecInfo(
            answer="ABC\n", elapsed=1.25, memory=None, returncode=0
        ),
        expected=make_result(
            name="default",
            status=JudgeStatus.AC,
        ),
        expected_log=[
            LogComparer("default: start"),
            LogComparer("default: \x1b[32mAC\x1b[39m, time: 1.250000 sec"),
        ],
    ),
    SingleCaseParams(
        name="Nones",
        inbytes=b"",
        outbytes=b"",
        mock_measure=OjExecInfo(answer=None, elapsed=1.25, memory=None, returncode=0),
        expected=make_result(
            name="Nones",
            status=JudgeStatus.AC,
        ),
        expected_log=[
            LogComparer("Nones: start"),
            LogComparer("Nones: \x1b[32mAC\x1b[39m, time: 1.250000 sec"),
        ],
    ),
    SingleCaseParams(
        name="memory",
        inbytes=b"",
        outbytes=b"19\n20\n",
        mock_measure=OjExecInfo(
            answer="19\n20\n", elapsed=1.25, memory=10.7, returncode=0
        ),
        expected=make_result(
            name="memory",
            memory=10.7,
            status=JudgeStatus.AC,
        ),
        expected_log=[
            LogComparer("memory: start"),
            LogComparer(
                "memory: \x1b[32mAC\x1b[39m, time: 1.250000 sec, memory: 10.700000 MB"
            ),
        ],
    ),
    SingleCaseParams(
        name="spaces",
        inbytes=b"foo \t bar\nbaz\t \r\nhoge\r\nfuga\n",
        outbytes=b"1\n",
        mock_measure=OjExecInfo(answer="2\n", elapsed=1.25, memory=None, returncode=0),
        expected=make_result(
            name="spaces",
            status=JudgeStatus.WA,
        ),
        expected_log=[
            LogComparer("spaces: start"),
            LogComparer(
                "spaces:input: "
                "\x1b[1mfoo\x1b[0m\x1b[2m_\\t_\x1b[0m\x1b[1mbar\x1b[0m\x1b[2m\\n"
                "\x1b[0m\x1b[1mbaz\x1b[0m\x1b[2m\\t_\x1b[0m\x1b[2m(trailing whitespace)\x1b[0m\x1b[2m\\n"
                "\x1b[0m\x1b[1mhoge\x1b[0m\x1b[2m\\n\x1b[0m\x1b[1mfuga\x1b[0m\x1b[2m\\n\x1b[0m",
            ),
            LogComparer("spaces:answer: \x1b[1m2\x1b[0m\x1b[2m\\n\x1b[0m"),
            LogComparer("spaces:expected: \x1b[1m1\x1b[0m\x1b[2m\\n\x1b[0m"),
            LogComparer("spaces: \x1b[31mWA\x1b[39m, time: 1.250000 sec"),
        ],
    ),
    SingleCaseParams(
        name="empty-lines",
        inbytes=b"\n\n\n\n",
        outbytes=b"1\n",
        mock_measure=OjExecInfo(answer="2\n", elapsed=1.25, memory=None, returncode=0),
        expected=make_result(
            name="empty-lines",
            status=JudgeStatus.WA,
        ),
        expected_log=[
            LogComparer("empty-lines: start"),
            LogComparer("empty-lines:input: \x1b[2m\\n\\n\\n\\n\x1b[0m"),
            LogComparer("empty-lines:answer: \x1b[1m2\x1b[0m\x1b[2m\\n\x1b[0m"),
            LogComparer("empty-lines:expected: \x1b[1m1\x1b[0m\x1b[2m\\n\x1b[0m"),
            LogComparer("empty-lines: \x1b[31mWA\x1b[39m, time: 1.250000 sec"),
        ],
    ),
    SingleCaseParams(
        name="judge-AC",
        inbytes=b"abc\n",
        outbytes=b"ABC\n",
        mock_judge=True,
        mock_measure=OjExecInfo(
            answer="ABC\n", elapsed=1.25, memory=None, returncode=0
        ),
        expected=make_result(
            name="judge-AC",
            status=JudgeStatus.AC,
        ),
        expected_log=[
            LogComparer("judge-AC: start"),
            LogComparer("judge-AC: \x1b[32mAC\x1b[39m, time: 1.250000 sec"),
        ],
    ),
    SingleCaseParams(
        name="judge-WA",
        inbytes=b"abc\n",
        outbytes=b"ABC\n",
        mock_judge=False,
        mock_measure=OjExecInfo(
            answer="ABC\n", elapsed=1.25, memory=None, returncode=0
        ),
        expected=make_result(
            name="judge-WA",
            status=JudgeStatus.WA,
        ),
        expected_log=[
            LogComparer("judge-WA: start"),
            LogComparer("judge-WA:input: \x1b[1mabc\x1b[0m\x1b[2m\\n\x1b[0m"),
            LogComparer("judge-WA:answer: \x1b[1mABC\x1b[0m\x1b[2m\\n\x1b[0m"),
            LogComparer("judge-WA:expected: \x1b[1mABC\x1b[0m\x1b[2m\\n\x1b[0m"),
            LogComparer("judge-WA: \x1b[31mWA\x1b[39m, time: 1.250000 sec"),
        ],
    ),
    SingleCaseParams(
        name="judge-WA-no-expected-out",
        inbytes=b"abc\n",
        outbytes=b"",
        mock_judge=False,
        mock_measure=OjExecInfo(
            answer="ABC\n", elapsed=1.25, memory=None, returncode=0
        ),
        expected=make_result(
            name="judge-WA-no-expected-out",
            status=JudgeStatus.WA,
        ),
        expected_log=[
            LogComparer("judge-WA-no-expected-out: start"),
            LogComparer(
                "judge-WA-no-expected-out:input: \x1b[1mabc\x1b[0m\x1b[2m\\n\x1b[0m"
            ),
            LogComparer(
                "judge-WA-no-expected-out:answer: \x1b[1mABC\x1b[0m\x1b[2m\\n\x1b[0m"
            ),
            LogComparer("judge-WA-no-expected-out:expected: \x1b[2m(empty)\x1b[0m"),
            LogComparer(
                "judge-WA-no-expected-out: \x1b[31mWA\x1b[39m, time: 1.250000 sec"
            ),
        ],
    ),
    SingleCaseParams(
        name="check_output-WA",
        inbytes=b"abc\n",
        outbytes=b"ABC",
        mock_measure=OjExecInfo(
            answer="ABC\n", elapsed=1.25, memory=None, returncode=0
        ),
        expected=make_result(
            name="check_output-WA",
            status=JudgeStatus.WA,
        ),
        expected_log=[
            LogComparer("check_output-WA: start"),
            LogComparer(
                "This was AC if spaces and newlines were ignored.",
                level=logging.WARNING,
            ),
            LogComparer(
                "check_output-WA:input: \x1b[1mabc\x1b[0m\x1b[2m\\n\x1b[0m",
            ),
            LogComparer("check_output-WA:answer: \x1b[1mABC\x1b[0m\x1b[2m\\n\x1b[0m"),
            LogComparer(
                "check_output-WA:expected: \x1b[1mABC\x1b[0m\x1b[2m(no trailing newline)\x1b[0m",
            ),
            LogComparer("check_output-WA: \x1b[31mWA\x1b[39m, time: 1.250000 sec"),
        ],
    ),
    SingleCaseParams(
        name="check_output-AC",
        inbytes=b"abc\n",
        outbytes=b"ABC\n",
        mock_measure=OjExecInfo(
            answer="ABC\n", elapsed=1.25, memory=None, returncode=0
        ),
        expected=make_result(
            name="check_output-AC",
            status=JudgeStatus.AC,
        ),
        expected_log=[
            LogComparer("check_output-AC: start"),
            LogComparer("check_output-AC: \x1b[32mAC\x1b[39m, time: 1.250000 sec"),
        ],
    ),
    SingleCaseParams(
        name="error-AC-equals",
        inbytes=b"Pi\n",
        outbytes=b"3.14159265358\n",
        error=1e-11,
        mock_measure=OjExecInfo(
            answer="3.14159265358\n", elapsed=1.25, memory=None, returncode=0
        ),
        expected=make_result(
            name="error-AC-equals",
            status=JudgeStatus.AC,
        ),
        expected_log=[
            LogComparer("error-AC-equals: start"),
            LogComparer("error-AC-equals: \x1b[32mAC\x1b[39m, time: 1.250000 sec"),
        ],
    ),
    SingleCaseParams(
        name="error-AC-long",
        inbytes=b"Pi\n",
        outbytes=b"3.141592653589793238462643383279502884197169399375105820974944592307816406286\n",
        error=1e-11,
        mock_measure=OjExecInfo(
            answer="3.14159265358\n", elapsed=1.25, memory=None, returncode=0
        ),
        expected=make_result(
            name="error-AC-long",
            status=JudgeStatus.AC,
        ),
        expected_log=[
            LogComparer("error-AC-long: start"),
            LogComparer("error-AC-long: \x1b[32mAC\x1b[39m, time: 1.250000 sec"),
        ],
    ),
    SingleCaseParams(
        name="error-AC-short",
        inbytes=b"Pi\n",
        outbytes=b"3.1415926536\n",
        error=1e-11,
        mock_measure=OjExecInfo(
            answer="3.14159265358\n", elapsed=1.25, memory=None, returncode=0
        ),
        expected=make_result(
            name="error-AC-short",
            status=JudgeStatus.AC,
        ),
        expected_log=[
            LogComparer("error-AC-short: start"),
            LogComparer("error-AC-short: \x1b[32mAC\x1b[39m, time: 1.250000 sec"),
        ],
    ),
    SingleCaseParams(
        name="error-small-AC-abs",
        inbytes=b"Planck mass\n",
        outbytes=b"0.0000000217640\n",
        error=1e-12,
        mock_measure=OjExecInfo(
            answer="0.0000000217647\n", elapsed=1.25, memory=None, returncode=0
        ),
        expected=make_result(
            name="error-small-AC-abs",
            status=JudgeStatus.AC,
        ),
        expected_log=[
            LogComparer("error-small-AC-abs: start"),
            LogComparer("error-small-AC-abs: \x1b[32mAC\x1b[39m, time: 1.250000 sec"),
        ],
    ),
    SingleCaseParams(
        name="error-small-AC-abs-short",
        inbytes=b"Planck mass\n",
        outbytes=b"0.000000021764\n",
        error=1e-12,
        mock_measure=OjExecInfo(
            answer="0.0000000217647\n", elapsed=1.25, memory=None, returncode=0
        ),
        expected=make_result(
            name="error-small-AC-abs-short",
            status=JudgeStatus.AC,
        ),
        expected_log=[
            LogComparer("error-small-AC-abs-short: start"),
            LogComparer(
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
            answer="0.0000000217647\n", elapsed=1.25, memory=None, returncode=0
        ),
        expected=make_result(
            name="error-small-WA-abs",
            status=JudgeStatus.WA,
        ),
        expected_log=[
            LogComparer("error-small-WA-abs: start"),
            LogComparer(
                "error-small-WA-abs:input: "
                "\x1b[1mPlanck\x1b[0m\x1b[2m_\x1b[0m\x1b[1mmass\x1b[0m\x1b[2m\\n\x1b[0m",
            ),
            LogComparer(
                "error-small-WA-abs:answer: \x1b[1m0.0000000217647\x1b[0m\x1b[2m\\n\x1b[0m",
            ),
            LogComparer(
                "error-small-WA-abs:expected: \x1b[1m0.0000000217640\x1b[0m\x1b[2m\\n\x1b[0m",
            ),
            LogComparer("error-small-WA-abs: \x1b[31mWA\x1b[39m, time: 1.250000 sec"),
        ],
    ),
    SingleCaseParams(
        name="error-large-AC-rel",
        inbytes=b"Planck temp\n",
        outbytes=b"141678400000000000000000000000000\n",
        error=1e-12,
        mock_measure=OjExecInfo(
            answer="141678400000000000000000000000000\n",
            elapsed=1.25,
            memory=None,
            returncode=0,
        ),
        expected=make_result(
            name="error-large-AC-rel",
            status=JudgeStatus.AC,
        ),
        expected_log=[
            LogComparer("error-large-AC-rel: start"),
            LogComparer("error-large-AC-rel: \x1b[32mAC\x1b[39m, time: 1.250000 sec"),
        ],
    ),
    SingleCaseParams(
        name="error-large-AC-rel-diff",
        inbytes=b"Planck temp\n",
        outbytes=b"141678400000000000000000000000000\n",
        error=1e-12,
        mock_measure=OjExecInfo(
            answer="141678400000021987654321987654321\n",
            elapsed=1.25,
            memory=None,
            returncode=0,
        ),
        expected=make_result(
            name="error-large-AC-rel-diff",
            status=JudgeStatus.AC,
        ),
        expected_log=[
            LogComparer("error-large-AC-rel-diff: start"),
            LogComparer(
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
            answer="141678400000021987654321987654321\n",
            elapsed=1.25,
            memory=None,
            returncode=0,
        ),
        expected=make_result(
            name="error-large-WA-rel",
            status=JudgeStatus.WA,
        ),
        expected_log=[
            LogComparer("error-large-WA-rel: start"),
            LogComparer(
                "error-large-WA-rel:input: "
                "\x1b[1mPlanck\x1b[0m\x1b[2m_\x1b[0m\x1b[1mtemp\x1b[0m\x1b[2m\\n\x1b[0m",
            ),
            LogComparer(
                "error-large-WA-rel:answer: \x1b[1m141678400000021987654321987654321\x1b[0m\x1b[2m\\n\x1b[0m",
            ),
            LogComparer(
                "error-large-WA-rel:expected: \x1b[1m141678400000000000000000000000000\x1b[0m\x1b[2m\\n\x1b[0m",
            ),
            LogComparer("error-large-WA-rel: \x1b[31mWA\x1b[39m, time: 1.250000 sec"),
        ],
    ),
    SingleCaseParams(
        name="lines-same",
        inbytes=b"abc\n",
        outbytes=b"ABC\nDEF\nGH\n",
        mock_measure=OjExecInfo(
            answer="ABC\nDEF\nGH\n", elapsed=1.25, memory=None, returncode=0
        ),
        expected=make_result(
            name="lines-same",
            status=JudgeStatus.AC,
        ),
        expected_log=[
            LogComparer("lines-same: start"),
            LogComparer("lines-same: \x1b[32mAC\x1b[39m, time: 1.250000 sec"),
        ],
    ),
    SingleCaseParams(
        name="lines-crlf",
        inbytes=b"abc\n",
        outbytes=b"ABC\nDEF\nGH\n",
        mock_measure=OjExecInfo(
            answer="ABC\r\nDEF\r\nGH\r\n", elapsed=1.25, memory=None, returncode=0
        ),
        expected=make_result(
            name="lines-crlf",
            status=JudgeStatus.AC,
        ),
        expected_log=[
            LogComparer("lines-crlf: start"),
            LogComparer("lines-crlf: \x1b[32mAC\x1b[39m, time: 1.250000 sec"),
        ],
    ),
    SingleCaseParams(
        name="lines-diff",
        inbytes=b"abc\n",
        outbytes=b"ABC\nDEF\nGH\n",
        mock_measure=OjExecInfo(
            answer="ABC\nDDF\nGH\n", elapsed=1.25, memory=None, returncode=0
        ),
        expected=make_result(
            name="lines-diff",
            status=JudgeStatus.WA,
        ),
        expected_log=[
            LogComparer("lines-diff: start"),
            LogComparer("lines-diff:input: \x1b[1mabc\x1b[0m\x1b[2m\\n\x1b[0m"),
            LogComparer(
                "lines-diff:answer: "
                "\x1b[1mABC\x1b[0m\x1b[2m\\n\x1b[0m\x1b[1mDDF\x1b[0m\x1b[2m\\n\x1b[0m\x1b[1mGH\x1b[0m\x1b[2m\\n\x1b[0m",
            ),
            LogComparer(
                "lines-diff:expected: "
                "\x1b[1mABC\x1b[0m\x1b[2m\\n\x1b[0m\x1b[1mDEF\x1b[0m\x1b[2m\\n\x1b[0m\x1b[1mGH\x1b[0m\x1b[2m\\n\x1b[0m",
            ),
            LogComparer("lines-diff: \x1b[31mWA\x1b[39m, time: 1.250000 sec"),
        ],
    ),
    SingleCaseParams(
        name="lines-error-diff-len",
        inbytes=b"abc\n",
        outbytes=b"ABC\nDEF\n3.14159265358979\n",
        error=1e-5,
        mock_measure=OjExecInfo(
            answer="ABC\nDEF\n3.14159265\n", elapsed=1.25, memory=None, returncode=0
        ),
        expected=make_result(
            name="lines-error-diff-len",
            status=JudgeStatus.AC,
        ),
        expected_log=[
            LogComparer("lines-error-diff-len: start"),
            LogComparer("lines-error-diff-len: \x1b[32mAC\x1b[39m, time: 1.250000 sec"),
        ],
    ),
    SingleCaseParams(
        name="lines-error-grid",
        inbytes=b"abc\n",
        outbytes=b"ABC CD\nDEF 3.141592653589\n3.14159265358979\n",
        error=1e-5,
        mock_measure=OjExecInfo(
            answer="ABC CD\nDEF 3.14159265\n3.14159265\n",
            elapsed=1.25,
            memory=None,
            returncode=0,
        ),
        expected=make_result(
            name="lines-error-grid",
            status=JudgeStatus.AC,
        ),
        expected_log=[
            LogComparer("lines-error-grid: start"),
            LogComparer("lines-error-grid: \x1b[32mAC\x1b[39m, time: 1.250000 sec"),
        ],
    ),
    SingleCaseParams(
        name="lines-grid-diff",
        inbytes=b"abc\n",
        outbytes=b"ABC CD\nDEF 3.141592653589\n3.14159265358979\n",
        error=1e-5,
        mock_measure=OjExecInfo(
            answer="ABC CD\nDEF 3.14159265 3.14\n3.14159265\n",
            elapsed=1.25,
            memory=None,
            returncode=0,
        ),
        expected=make_result(
            name="lines-grid-diff",
            status=JudgeStatus.WA,
        ),
        expected_log=[
            LogComparer("lines-grid-diff: start"),
            LogComparer("lines-grid-diff:input: \x1b[1mabc\x1b[0m\x1b[2m\\n\x1b[0m"),
            LogComparer(
                "lines-grid-diff:answer: "
                "\x1b[1mABC\x1b[0m\x1b[2m_\x1b[0m\x1b[1mCD\x1b[0m\x1b[2m\\n"
                "\x1b[0m\x1b[1mDEF\x1b[0m\x1b[2m_\x1b[0m\x1b[1m3.14159265\x1b[0m\x1b[2m_\x1b[0m\x1b[1m3.14\x1b[0m\x1b[2m\\n"
                "\x1b[0m\x1b[1m3.14159265\x1b[0m\x1b[2m\\n\x1b[0m",
            ),
            LogComparer(
                "lines-grid-diff:expected: "
                "\x1b[1mABC\x1b[0m\x1b[2m_\x1b[0m\x1b[1mCD\x1b[0m\x1b[2m\\n"
                "\x1b[0m\x1b[1mDEF\x1b[0m\x1b[2m_\x1b[0m\x1b[1m3.141592653589\x1b[0m\x1b[2m\\n"
                "\x1b[0m\x1b[1m3.14159265358979\x1b[0m\x1b[2m\\n\x1b[0m",
            ),
            LogComparer("lines-grid-diff: \x1b[31mWA\x1b[39m, time: 1.250000 sec"),
        ],
    ),
    SingleCaseParams(
        name="lines-grid-diff-lines",
        inbytes=b"abc\n",
        outbytes=b"ABC CD\nDEF 3.141592653589\n3.14159265358979\n",
        error=1e-5,
        mock_measure=OjExecInfo(
            answer="ABC CD\nDEF 3.14159265 3.14\n3.14159265\nno\n",
            elapsed=1.25,
            memory=None,
            returncode=0,
        ),
        expected=make_result(
            name="lines-grid-diff-lines",
            status=JudgeStatus.WA,
        ),
        expected_log=[
            LogComparer("lines-grid-diff-lines: start"),
            LogComparer(
                "lines-grid-diff-lines:input: \x1b[1mabc\x1b[0m\x1b[2m\\n\x1b[0m"
            ),
            LogComparer(
                "lines-grid-diff-lines:answer: "
                "\x1b[1mABC\x1b[0m\x1b[2m_\x1b[0m\x1b[1mCD\x1b[0m\x1b[2m\\n"
                "\x1b[0m\x1b[1mDEF\x1b[0m\x1b[2m_\x1b[0m\x1b[1m3.14159265\x1b[0m\x1b[2m_\x1b[0m\x1b[1m3.14\x1b[0m\x1b[2m\\n"
                "\x1b[0m\x1b[1m3.14159265\x1b[0m\x1b[2m\\n\x1b[0m\x1b[1mno\x1b[0m\x1b[2m\\n\x1b[0m",
            ),
            LogComparer(
                "lines-grid-diff-lines:expected: "
                "\x1b[1mABC\x1b[0m\x1b[2m_\x1b[0m\x1b[1mCD\x1b[0m\x1b[2m\\n"
                "\x1b[0m\x1b[1mDEF\x1b[0m\x1b[2m_\x1b[0m\x1b[1m3.141592653589\x1b[0m\x1b[2m\\n"
                "\x1b[0m\x1b[1m3.14159265358979\x1b[0m\x1b[2m\\n\x1b[0m",
            ),
            LogComparer(
                "lines-grid-diff-lines: \x1b[31mWA\x1b[39m, time: 1.250000 sec"
            ),
        ],
    ),
    SingleCaseParams(
        name="error-str-same",
        inbytes=b"abc\n",
        outbytes=b"ABC\n",
        error=1e-3,
        mock_measure=OjExecInfo(
            answer="ABC\n", elapsed=1.25, memory=None, returncode=0
        ),
        expected=make_result(
            name="error-str-same",
            status=JudgeStatus.AC,
        ),
        expected_log=[
            LogComparer("error-str-same: start"),
            LogComparer("error-str-same: \x1b[32mAC\x1b[39m, time: 1.250000 sec"),
        ],
    ),
    SingleCaseParams(
        name="error-str-WA",
        inbytes=b"abc\n",
        outbytes=b"DEF\n",
        error=1e-3,
        mock_measure=OjExecInfo(
            answer="ABC\n", elapsed=1.25, memory=None, returncode=0
        ),
        expected=make_result(
            name="error-str-WA",
            status=JudgeStatus.WA,
        ),
        expected_log=[
            LogComparer("error-str-WA: start"),
            LogComparer("error-str-WA:input: \x1b[1mabc\x1b[0m\x1b[2m\\n\x1b[0m"),
            LogComparer("error-str-WA:answer: \x1b[1mABC\x1b[0m\x1b[2m\\n\x1b[0m"),
            LogComparer("error-str-WA:expected: \x1b[1mDEF\x1b[0m\x1b[2m\\n\x1b[0m"),
            LogComparer("error-str-WA: \x1b[31mWA\x1b[39m, time: 1.250000 sec"),
        ],
    ),
    SingleCaseParams(
        name="TLE",
        inbytes=b"abc\n",
        outbytes=b"ABC\n",
        mock_measure=OjExecInfo(
            answer="ABC\n", elapsed=1.25, memory=None, returncode=None
        ),
        expected=make_result(
            name="TLE",
            exitcode=None,
            status=JudgeStatus.TLE,
        ),
        expected_log=[
            LogComparer("TLE: start"),
            LogComparer("TLE:input: \x1b[1mabc\x1b[0m\x1b[2m\\n\x1b[0m"),
            LogComparer("TLE:expected: \x1b[1mABC\x1b[0m\x1b[2m\\n\x1b[0m"),
            LogComparer("TLE: \x1b[31mTLE\x1b[39m, time: 1.250000 sec"),
        ],
    ),
    SingleCaseParams(
        name="RE",
        inbytes=b"abc\n",
        outbytes=b"ABC\n",
        mock_measure=OjExecInfo(
            answer="ABC\n", elapsed=1.25, memory=None, returncode=1
        ),
        expected=make_result(
            name="RE",
            exitcode=1,
            status=JudgeStatus.RE,
        ),
        expected_log=[
            LogComparer("RE: start"),
            LogComparer("RE:input: \x1b[1mabc\x1b[0m\x1b[2m\\n\x1b[0m"),
            LogComparer("RE:expected: \x1b[1mABC\x1b[0m\x1b[2m\\n\x1b[0m"),
            LogComparer("RE: \x1b[31mRE\x1b[39m, time: 1.250000 sec, return code: 1"),
        ],
    ),
    SingleCaseParams(
        name="MLE-NotMeasure",
        inbytes=b"abc\n",
        outbytes=b"ABC\n",
        mle=128,
        mock_measure=OjExecInfo(
            answer="ABC\n", elapsed=1.25, memory=None, returncode=0
        ),
        expected=make_result(
            name="MLE-NotMeasure",
            status=JudgeStatus.AC,
        ),
        expected_log=[
            LogComparer("MLE-NotMeasure: start"),
            LogComparer("MLE-NotMeasure: \x1b[32mAC\x1b[39m, time: 1.250000 sec"),
        ],
    ),
    SingleCaseParams(
        name="MLE-Safe",
        inbytes=b"abc\n",
        outbytes=b"ABC\n",
        mle=128,
        mock_measure=OjExecInfo(answer="ABC\n", elapsed=1.25, memory=128, returncode=0),
        expected=make_result(
            name="MLE-Safe",
            memory=128,
            status=JudgeStatus.AC,
        ),
        expected_log=[
            LogComparer("MLE-Safe: start"),
            LogComparer(
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
            answer="ABC\n", elapsed=1.25, memory=128.1, returncode=1
        ),
        expected=make_result(
            name="MLE",
            exitcode=1,
            memory=128.1,
            status=JudgeStatus.MLE,
        ),
        expected_log=[
            LogComparer("MLE: start"),
            LogComparer("MLE:input: \x1b[1mabc\x1b[0m\x1b[2m\\n\x1b[0m"),
            LogComparer("MLE:answer: \x1b[1mABC\x1b[0m\x1b[2m\\n\x1b[0m"),
            LogComparer("MLE:expected: \x1b[1mABC\x1b[0m\x1b[2m\\n\x1b[0m"),
            LogComparer(
                "MLE: \x1b[31mMLE\x1b[39m,"
                " time: 1.250000 sec, memory: 128.100000 MB, return code: 1"
            ),
        ],
    ),
    SingleCaseParams(
        name="long-lines",
        inbytes=b"abc\n",
        outbytes=b"ABC\n",
        mock_measure=OjExecInfo(
            answer="""ea226088-3cc7-4d33-985c-00004dfcdccb
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
            status=JudgeStatus.WA,
        ),
        expected_log=[
            LogComparer("long-lines: start"),
            LogComparer("long-lines:input: \x1b[1mabc\x1b[0m\x1b[2m\\n\x1b[0m"),
            LogComparer(
                "long-lines:answer: "
                "\x1b[1mea226088-3cc7-4d33-9\x1b[0m\x1b[2m... (145 chars) "
                "...\x1b[0m\x1b[1md-9f86-b0bba61f2608\x1b[0m\x1b[2m\\n\x1b[0m",
            ),
            LogComparer("long-lines:expected: \x1b[1mABC\x1b[0m\x1b[2m\\n\x1b[0m"),
            LogComparer("long-lines: \x1b[31mWA\x1b[39m, time: 1.250000 sec"),
        ],
    ),
    SingleCaseParams(
        name="long-text",
        inbytes=b"abc\r\n",
        outbytes=b"ABC\n",
        mock_measure=OjExecInfo(
            answer="ea226088-3cc7-4d33-985c-00004dfcdccb6f791930-4b08-4618-a110-32be65332f08"
            "87f28765-03bb-4aa3-ad2c-5e781aa60ca09b063b0f-7b48-4a1d-a49f-4e8524ace9174"
            "2e6d61b-9656-4cb6-be7a-1a5d80224390961bed54-a32d-47c7-bb82-ae4591ed8ccd\r\n",
            elapsed=1.25,
            memory=None,
            returncode=0,
        ),
        expected=make_result(
            name="long-text",
            status=JudgeStatus.WA,
        ),
        expected_log=[
            LogComparer("long-text: start"),
            LogComparer(
                "long-text:input: \x1b[1mabc\x1b[0m\x1b[2m\\n\x1b[0m",
            ),
            LogComparer(
                "long-text:answer: "
                "\x1b[1mea226088-3cc7-4d33-9\x1b[0m\x1b[2m... (178 chars) ...\x1b[0m"
                "\x1b[1m-bb82-ae4591ed8ccd\x1b[0m\x1b[2m\\r\\n\x1b[0m",
            ),
            LogComparer("long-text:expected: \x1b[1mABC\x1b[0m\x1b[2m\\n\x1b[0m"),
            LogComparer("long-text: \x1b[31mWA\x1b[39m, time: 1.250000 sec"),
        ],
    ),
    SingleCaseParams(
        name="long-lines-break",
        inbytes=b"abc\n",
        outbytes=b"ABC\n",
        mock_measure=OjExecInfo(
            answer="""ea226088-3cc7-4d33-\n985c-00004dfcdccb
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
            status=JudgeStatus.WA,
        ),
        expected_log=[
            LogComparer("long-lines-break: start"),
            LogComparer("long-lines-break:input: \x1b[1mabc\x1b[0m\x1b[2m\\n\x1b[0m"),
            LogComparer(
                "long-lines-break:answer: "
                "\x1b[1mea226088-3cc7-4d33-\x1b[0m\x1b[2m\\n\x1b[0m\x1b[2m... (147 chars) "
                "...\x1b[0m\x1b[2m\\n\x1b[0m\x1b[1m-9f86-b0bba61f2608\x1b[0m\x1b[2m\\n\x1b[0m",
            ),
            LogComparer(
                "long-lines-break:expected: \x1b[1mABC\x1b[0m\x1b[2m\\n\x1b[0m"
            ),
            LogComparer("long-lines-break: \x1b[31mWA\x1b[39m, time: 1.250000 sec"),
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
    outbytes: bytes,
    error: float | None,
    mle: float | None,
    expected: OjTestcaseResult,
    expected_log: list[LogComparer],
    caplog: pytest.LogCaptureFixture,
    mock_judge: Problem,
    mock_measure: OjExecInfo,
    testtemp: pathlib.Path,
):
    caplog.set_level(logging.NOTSET)
    input_path = testtemp / "infile"
    input_path.write_bytes(inbytes)

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

    expected.answer = mock_measure.answer or ""
    expected.input = input_path
    expected.expected = output_path
    assert result == expected
    assert caplog.records == expected_log


def test_single_case_error(
    mocker: MockerFixture,
    mock_judge: Problem,
    caplog: pytest.LogCaptureFixture,
    testtemp: pathlib.Path,
    subtests: pytest.Subtests,
):
    caplog.set_level(logging.NOTSET)
    input_path = testtemp / "infile"
    input_path.write_bytes(b"ABC")

    output_path = testtemp / "outfile"
    output_path.write_bytes(b"abc")

    expected = OjTestcaseResult(
        name="error",
        input=input_path,
        answer="",
        expected=output_path,
        status=JudgeStatus.RE,
        elapsed=0,
        exitcode=255,
    )

    mocker.patch("competitive_verifier.oj.gnu.time_command", return_value="time")
    for cmd in ["", ":no_exists:"]:
        with subtests.test(msg=cmd if cmd else "<empty>"):
            caplog.clear()
            assert (
                single_case(
                    "error",
                    test_input_path=input_path,
                    test_output_path=output_path,
                    args=OjTestArguments(
                        command=cmd,
                        problem=mock_judge,
                        error=None,
                        mle=None,
                        tle=None,
                    ),
                )
                == expected
            )
            assert caplog.records == [
                LogComparer("error: start"),
                LogComparer(
                    "Failed to run: OjTestArguments(command='" + cmd + "', "
                    "problem=AOJProblem.from_url('http://judge.u-aizu.ac.jp/onlinejudge/description.jsp?id=1'), "
                    "tle=None, mle=None, error=None, env=None, deadline=inf)",
                    level=logging.ERROR,
                    github=GitHubMessageParams(),
                ),
            ]
        with subtests.test(msg="Exception"):
            caplog.clear()
            mocker.patch("subprocess.Popen", side_effect=Exception)
            assert (
                single_case(
                    "error",
                    test_input_path=input_path,
                    test_output_path=output_path,
                    args=OjTestArguments(
                        command="git",
                        problem=mock_judge,
                        error=None,
                        mle=None,
                        tle=None,
                    ),
                )
                == expected
            )
            assert caplog.records[0] == LogComparer("error: start")
            assert caplog.records[2] == LogComparer(
                "Failed to run: OjTestArguments(command='git', "
                "problem=AOJProblem.from_url('http://judge.u-aizu.ac.jp/onlinejudge/description.jsp?id=1'), "
                "tle=None, mle=None, error=None, env=None, deadline=inf)",
                level=logging.ERROR,
                github=GitHubMessageParams(),
            )

            assert caplog.records[1].msg.endswith("is not executable.")


class GnuTimeMessageParam(NamedTuple):
    has_gnu_time: bool
    system: str
    mle: float | None
    expected: list[LogComparer]


test_gnu_time_message_params: list[GnuTimeMessageParam] = [
    GnuTimeMessageParam(True, "Darwin", 5.5, []),
    GnuTimeMessageParam(True, "Darwin", None, []),
    GnuTimeMessageParam(True, "Windows", 2, []),
    GnuTimeMessageParam(True, "Windows", None, []),
    GnuTimeMessageParam(
        False,
        "Darwin",
        5.5,
        [
            LogComparer(
                "[HINT]: You can install GNU time with: $ brew install gnu-time",
                logging.INFO,
                github=GitHubMessageParams(),
            ),
            LogComparer(
                "--mle is used but GNU time does not exist",
                logging.WARNING,
                github=GitHubMessageParams(),
            ),
        ],
    ),
    GnuTimeMessageParam(
        False,
        "Darwin",
        None,
        [
            LogComparer(
                "[HINT]: You can install GNU time with: $ brew install gnu-time",
                logging.INFO,
                github=GitHubMessageParams(),
            ),
        ],
    ),
    GnuTimeMessageParam(
        False,
        "Windows",
        2,
        [
            LogComparer(
                "--mle is used but GNU time does not exist",
                logging.WARNING,
                github=GitHubMessageParams(),
            ),
        ],
    ),
    GnuTimeMessageParam(
        False,
        "Windows",
        None,
        [],
    ),
]


@pytest.mark.parametrize(GnuTimeMessageParam._fields, test_gnu_time_message_params)
def test_gnu_time_message(
    has_gnu_time: bool,
    system: str,
    mle: float | None,
    expected: list[LogComparer],
    mock_judge: Problem,
    mocker: MockerFixture,
    caplog: pytest.LogCaptureFixture,
):
    caplog.set_level(0)
    mocker.patch(
        "competitive_verifier.oj.gnu.time_command",
        return_value="time" if has_gnu_time else None,
    )
    mocker.patch("platform.system", return_value=system)

    gnu_time_message(
        OjTestArguments("dummy", problem=mock_judge, tle=None, mle=mle, error=None)
    )
    assert caplog.records == expected


def test_timeout(
    mocker: MockerFixture,
    mock_judge: Problem,
    mock_perf_counter: MockType,
):
    single_case_mock = mocker.patch(
        "competitive_verifier.oj.oj_test.single_case",
        return_value=make_result(
            name="default",
            elapsed=1.25,
            memory=None,
            status=JudgeStatus.AC,
        ),
    )
    mocker.patch.object(
        mock_judge,
        "iter_system_cases",
        return_value=[
            SystemTestCaseFile(
                name=str(i),
                input_path=pathlib.Path(str(i)),
                output_path=pathlib.Path(str(i)),
            )
            for i in range(100)
        ],
    )

    with pytest.raises(VerifcationTimeoutError):
        oj.test(
            problem=mock_judge,
            command="dummy",
            env=None,
            tle=None,
            mle=None,
            error=None,
            deadline=2.99,
        )

    assert single_case_mock.call_count == 3


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


class MockCasesProblem(SystemTestCaseProvider):
    cases: list[SystemTestCaseFile]

    def __init__(self, cases: list[SystemTestCaseFile]) -> None:
        self.cases = cases

    def download_system_cases(self) -> Any:
        raise NotImplementedError

    def iter_system_cases(self) -> list[SystemTestCaseFile]:
        return self.cases


def test_oj_test_run(mocker: MockerFixture, subtests: pytest.Subtests):
    case_count = 0

    def infinite_case(*args: Any, **kwargs: Any):
        nonlocal case_count
        while True:
            case_count += 1
            return make_result(name=f"case{case_count}", status=JudgeStatus.AC)

    mocker.patch(
        "competitive_verifier.oj.oj_test.single_case",
        side_effect=infinite_case,
    )
    mock_summarize = mocker.patch("competitive_verifier.oj.oj_test.summarize")

    with subtests.test(msg="empty"):
        oj.test(
            problem=MockCasesProblem([]),
            command="dummy",
            env=None,
            tle=None,
            mle=None,
            error=None,
        )
        mock_summarize.assert_called_once_with([])

    with subtests.test(msg="three"):
        mock_summarize.reset_mock()
        oj.test(
            problem=MockCasesProblem(
                [
                    SystemTestCaseFile(
                        name=f"c{i}",
                        input_path=pathlib.Path(),
                        output_path=pathlib.Path(),
                    )
                    for i in range(3)
                ]
            ),
            command="dummy",
            env=None,
            tle=None,
            mle=None,
            error=None,
        )
        mock_summarize.assert_called_once_with(
            [
                make_result(name="case1", status=JudgeStatus.AC),
                make_result(name="case2", status=JudgeStatus.AC),
                make_result(name="case3", status=JudgeStatus.AC),
            ]
        )


def test_compare_answer_too_large_error(
    mocker: MockerFixture,
    caplog: pytest.LogCaptureFixture,
):
    mocker.patch("competitive_verifier.oj.oj_test.summarize")

    oj.test(
        problem=MockCasesProblem([]),
        command="dummy",
        env=None,
        tle=None,
        mle=None,
        error=0.9999,
    )
    assert not caplog.records

    oj.test(
        problem=MockCasesProblem([]),
        command="dummy",
        env=None,
        tle=None,
        mle=None,
        error=1.0001,
    )

    assert caplog.records == [
        LogComparer(
            "the tolerance is too large: relative = 1.0001",
            logging.WARNING,
            github=GitHubMessageParams(),
        ),
    ]


EXPECTED_CASES = cast("list[OjTestcaseResult]", ...)
test_summarize_params = [
    pytest.param(
        [],
        OjTestResult(
            is_success=True,
            elapsed=0,
            slowest=-1.0,
            heaviest=-1.0,
            testcases=EXPECTED_CASES,
        ),
        [
            LogComparer("\x1b[32mSUCCESS\x1b[39m 0 cases"),
        ],
        id="empty",
    ),
    pytest.param(
        [
            make_result(
                f"case{i}",
                status=JudgeStatus.AC,
                elapsed=i * 0.5,
                memory=i * 1.5,
            )
            for i in [9, 6, 5, 8, 1, 2, 3, 4, 7, 0]
        ],
        OjTestResult(
            is_success=True,
            elapsed=45 / 2,
            slowest=9 / 2,
            heaviest=9 * 1.5,
            testcases=EXPECTED_CASES,
        ),
        [
            LogComparer("slowest: 4.500000 sec  (for case9)"),
            LogComparer("max memory: 13.500000 MB  (for case9)"),
            LogComparer("\x1b[32mSUCCESS\x1b[39m 10 cases"),
        ],
        id="shuffle",
    ),
    pytest.param(
        [
            make_result(
                f"case{i}",
                status=JudgeStatus.AC,
                elapsed=i * 0.5,
            )
            for i in [9, 6, 5, 8, 1, 2, 3, 4, 7, 0]
        ],
        OjTestResult(
            is_success=True,
            elapsed=45 / 2,
            slowest=9 / 2,
            heaviest=-1.0,
            testcases=EXPECTED_CASES,
        ),
        [
            LogComparer("slowest: 4.500000 sec  (for case9)"),
            LogComparer("\x1b[32mSUCCESS\x1b[39m 10 cases"),
        ],
        id="no_memory",
    ),
    pytest.param(
        [
            make_result(
                f"case{i}",
                status=st,
                elapsed=i * 0.5,
                memory=i * 1.5,
            )
            for i, st in enumerate(
                chain(
                    *(
                        [st] * cnt
                        for st, cnt in zip(
                            list(JudgeStatus), range(1, 10000), strict=False
                        )
                    )
                )
            )
        ],
        OjTestResult(
            is_success=False,
            elapsed=(3 * len(JudgeStatus) - 1) * (3 * len(JudgeStatus)) / 2 / 2,
            slowest=(3 * len(JudgeStatus) - 1) / 2,
            heaviest=(3 * len(JudgeStatus) - 1) * 1.5,
            testcases=EXPECTED_CASES,
        ),
        [
            LogComparer("slowest: 7.000000 sec  (for case14)"),
            LogComparer("max memory: 21.000000 MB  (for case14)"),
            LogComparer(
                "\x1b[31mFAILURE\x1b[39m 1 AC, 2 WA, 3 RE, 4 TLE, 5 MLE / 15 cases",
            ),
        ],
        id="statuses",
    ),
]


@pytest.mark.parametrize(("history", "expected", "expected_log"), test_summarize_params)
def test_summarize(
    history: list[OjTestcaseResult],
    expected: OjTestResult,
    expected_log: list[tuple[str, int, str]],
    caplog: pytest.LogCaptureFixture,
):
    caplog.set_level(0)
    expected.testcases = history
    assert summarize(history) == expected
    assert caplog.records == expected_log


test_special_judge_params = [
    (
        None,
        None,
        False,
        [
            LogComparer(
                "judge's output: \x1b[2m(empty)\x1b[0m",
                10,
            )
        ],
    ),
    (
        "a b c",
        1,
        False,
        [
            LogComparer(
                "judge's output: "
                "\x1b[1ma\x1b[0m\x1b[2m_\x1b[0m\x1b[1mb\x1b[0m\x1b[2m_\x1b[0m\x1b[1mc\x1b[0m"
                "\x1b[2m(no trailing newline)\x1b[0m",
                10,
            )
        ],
    ),
    (
        "ABC\n",
        0,
        True,
        [
            LogComparer(
                "judge's output: \x1b[1mABC\x1b[0m\x1b[2m\\n\x1b[0m",
                10,
            )
        ],
    ),
]


@pytest.mark.parametrize(
    ("answer", "returncode", "expected", "expected_log"),
    test_special_judge_params,
)
def test_special_judge(
    answer: str | None,
    returncode: int | None,
    expected: bool,
    expected_log: list[LogComparer],
    mocker: MockerFixture,
    testtemp: pathlib.Path,
    caplog: pytest.LogCaptureFixture,
):
    caplog.set_level(0)
    mock_measure = mocker.patch(
        "competitive_verifier.oj.oj_test.measure_command",
        return_value=OjExecInfo(
            answer=answer, elapsed=0, memory=None, returncode=returncode
        ),
    )
    assert (
        special_judge(
            "/special/check",
            "a b c\n",
            input_path=testtemp / "input",
            expected_output_path=testtemp / "expected",
        )
        == expected
    )

    check_cmd = [
        "/special/check",
        str(testtemp / "input"),
        str(testtemp / "1/actual.out"),
        str(testtemp / "expected"),
    ]
    mock_measure.assert_called_once_with(check_cmd)
    assert caplog.records[0] == LogComparer(
        f"$ {check_cmd!s}",
        10,
    )
    assert caplog.records[1:] == expected_log
