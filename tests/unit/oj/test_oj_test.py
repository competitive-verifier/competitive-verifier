import logging
import os
import pathlib
from typing import Any, NamedTuple, TypedDict

import pytest
from pytest_mock import MockerFixture

from competitive_verifier.models import JudgeStatus
from competitive_verifier.oj.tools.oj_test import (
    OjExecInfo,
    OjTestArguments,
    SpecialJudge,
    single_case,
)

OJ_TEST_MODULE = "competitive_verifier.oj.tools.oj_test"


@pytest.fixture
def mock_measure(
    mocker: MockerFixture,
    request: pytest.FixtureRequest,
):
    assert isinstance(request.param, OjExecInfo)

    mocker.patch(
        "competitive_verifier.oj.tools.oj_test.measure_command",
        return_value=request.param,
    )


@pytest.fixture
def mock_terminal_size(mocker: MockerFixture):
    mocker.patch("shutil.get_terminal_size", return_value=os.terminal_size((60, 0)))


@pytest.fixture
def mock_judge(
    mocker: MockerFixture,
    request: pytest.FixtureRequest,
) -> bool:
    assert request.param is None or isinstance(request.param, bool)

    if request.param is not None:
        mocker.patch.object(SpecialJudge, "run", return_value=request.param)
        return True
    return False


class _OjTestcaseResultDict(TypedDict):
    name: str
    elapsed: float
    exitcode: int | None
    memory: float | None
    status: JudgeStatus


class SingleCaseParams(NamedTuple):
    name: str
    inbytes: bytes
    mock_measure: OjExecInfo
    expected: _OjTestcaseResultDict
    expected_log: list[tuple[str, int, str]]
    outbytes: bytes | None = None
    error: float | None = None
    mle: float | None = None
    judge: bool | None = None


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
        expected={
            "name": "default",
            "elapsed": 1.25,
            "exitcode": 0,
            "memory": None,
            "status": JudgeStatus.AC,
        },
        expected_log=[
            log_output("default"),
            log_output("time: 1.250000 sec"),
            log_output("SUCCESS: \x1b[32mAC\x1b[39m"),
        ],
    ),
    SingleCaseParams(
        name="no_output",
        inbytes=b"abc\n",
        mock_measure=OjExecInfo(
            answer=b"ABC\n", elapsed=1.25, memory=None, returncode=0
        ),
        expected={
            "name": "no_output",
            "elapsed": 1.25,
            "exitcode": 0,
            "memory": None,
            "status": JudgeStatus.AC,
        },
        expected_log=[
            log_output("no_output"),
            log_output("time: 1.250000 sec"),
            log_output(
                "input:\n\x1b[1mabc\x1b[0m\x1b[2m\\n\x1b[0m",
            ),
            log_output("output:\n\x1b[1mABC\x1b[0m\x1b[2m\\n\x1b[0m"),
            log_output("SUCCESS: \x1b[32mAC\x1b[39m"),
        ],
    ),
    SingleCaseParams(
        name="Nones",
        inbytes=b"",
        mock_measure=OjExecInfo(answer=None, elapsed=1.25, memory=None, returncode=0),
        expected={
            "name": "Nones",
            "elapsed": 1.25,
            "exitcode": 0,
            "memory": None,
            "status": JudgeStatus.AC,
        },
        expected_log=[
            log_output("Nones"),
            log_output("time: 1.250000 sec"),
            log_output("input:\n\x1b[2m(empty)\x1b[0m"),
            log_output("output:\n\x1b[2m(empty)\x1b[0m"),
            log_output("SUCCESS: \x1b[32mAC\x1b[39m"),
        ],
    ),
    SingleCaseParams(
        name="memory",
        inbytes=b"",
        mock_measure=OjExecInfo(
            answer=b"19\n20", elapsed=1.25, memory=10.7, returncode=0
        ),
        expected={
            "name": "memory",
            "elapsed": 1.25,
            "exitcode": 0,
            "memory": 10.7,
            "status": JudgeStatus.AC,
        },
        expected_log=[
            log_output("memory"),
            log_output("time: 1.250000 sec, memory: 10.700000 MB"),
            log_output("input:\n\x1b[2m(empty)\x1b[0m"),
            log_output(
                msg="output:\n"
                "\x1b[1m19\x1b[0m\x1b[2m\\n\x1b[0m\x1b[1m20\x1b[0m\x1b[2m(no trailing newline)\x1b[0m",
            ),
            log_output("SUCCESS: \x1b[32mAC\x1b[39m"),
        ],
    ),
    SingleCaseParams(
        name="spaces",
        inbytes=b"foo \t bar\nbaz \r\nhoge\nfuga\n",
        mock_measure=OjExecInfo(answer=None, elapsed=1.25, memory=None, returncode=0),
        expected={
            "name": "spaces",
            "elapsed": 1.25,
            "exitcode": 0,
            "memory": None,
            "status": JudgeStatus.AC,
        },
        expected_log=[
            log_output("spaces"),
            log_output("time: 1.250000 sec"),
            log_output(
                "input:\n"
                "\x1b[1mfoo\x1b[0m\x1b[2m_\\t_\x1b[0m\x1b[1mbar\x1b[0m\x1b[2m\\n"
                "\x1b[0m\x1b[1mbaz\x1b[0m\x1b[2m_\\r\x1b[0m\x1b[2m(trailing whitespace)\x1b[0m\x1b[2m\\n"
                "\x1b[0m\x1b[1mhoge\x1b[0m\x1b[2m\\n\x1b[0m\x1b[1mfuga\x1b[0m\x1b[2m\\n\x1b[0m",
            ),
            log_output("output:\n\x1b[2m(empty)\x1b[0m"),
            log_output("SUCCESS: \x1b[32mAC\x1b[39m"),
        ],
    ),
    SingleCaseParams(
        name="empty-lines",
        inbytes=b"\n\n\n\n",
        mock_measure=OjExecInfo(answer=None, elapsed=1.25, memory=None, returncode=0),
        expected={
            "name": "empty-lines",
            "elapsed": 1.25,
            "exitcode": 0,
            "memory": None,
            "status": JudgeStatus.AC,
        },
        expected_log=[
            log_output("empty-lines"),
            log_output("time: 1.250000 sec"),
            log_output("input:\n\x1b[2m\\n\\n\\n\\n\x1b[0m"),
            log_output("output:\n\x1b[2m(empty)\x1b[0m"),
            log_output("SUCCESS: \x1b[32mAC\x1b[39m"),
        ],
    ),
    SingleCaseParams(
        name="judge-AC",
        inbytes=b"abc\n",
        outbytes=b"ABC\n",
        judge=True,
        mock_measure=OjExecInfo(
            answer=b"ABC\n", elapsed=1.25, memory=None, returncode=0
        ),
        expected={
            "name": "judge-AC",
            "elapsed": 1.25,
            "exitcode": 0,
            "memory": None,
            "status": JudgeStatus.AC,
        },
        expected_log=[
            log_output("judge-AC"),
            log_output("time: 1.250000 sec"),
            log_output("SUCCESS: \x1b[32mAC\x1b[39m"),
        ],
    ),
    SingleCaseParams(
        name="judge-WA",
        inbytes=b"abc\n",
        outbytes=b"ABC\n",
        judge=False,
        mock_measure=OjExecInfo(
            answer=b"ABC\n", elapsed=1.25, memory=None, returncode=0
        ),
        expected={
            "name": "judge-WA",
            "elapsed": 1.25,
            "exitcode": 0,
            "memory": None,
            "status": JudgeStatus.WA,
        },
        expected_log=[
            log_output("judge-WA"),
            log_output("time: 1.250000 sec"),
            log_output("FAILURE: \x1b[31mWA\x1b[39m"),
            log_output("input:\n\x1b[1mabc\x1b[0m\x1b[2m\\n\x1b[0m"),
            log_output("output:\n\x1b[1mABC\x1b[0m\x1b[2m\\n\x1b[0m"),
            log_output("expected:\n\x1b[1mABC\x1b[0m\x1b[2m\\n\x1b[0m"),
        ],
    ),
    SingleCaseParams(
        name="judge-WA-no-expected-out",
        inbytes=b"abc\n",
        judge=False,
        mock_measure=OjExecInfo(
            answer=b"ABC\n", elapsed=1.25, memory=None, returncode=0
        ),
        expected={
            "name": "judge-WA-no-expected-out",
            "elapsed": 1.25,
            "exitcode": 0,
            "memory": None,
            "status": JudgeStatus.WA,
        },
        expected_log=[
            log_output("judge-WA-no-expected-out"),
            log_output("time: 1.250000 sec"),
            log_output("expected output is not found", level=logging.WARNING),
            log_output("FAILURE: \x1b[31mWA\x1b[39m", level=logging.INFO),
            log_output("input:\n\x1b[1mabc\x1b[0m\x1b[2m\\n\x1b[0m"),
            log_output("output:\n\x1b[1mABC\x1b[0m\x1b[2m\\n\x1b[0m"),
            log_output("expected:\n\x1b[2m(empty)\x1b[0m"),
        ],
    ),
    SingleCaseParams(
        name="check_output-WA",
        inbytes=b"abc\n",
        outbytes=b"ABC",
        mock_measure=OjExecInfo(
            answer=b"ABC\n", elapsed=1.25, memory=None, returncode=0
        ),
        expected={
            "name": "check_output-WA",
            "elapsed": 1.25,
            "exitcode": 0,
            "memory": None,
            "status": JudgeStatus.WA,
        },
        expected_log=[
            log_output("check_output-WA"),
            log_output("time: 1.250000 sec"),
            log_output(
                "This was AC if spaces and newlines were ignored.",
                level=logging.WARNING,
            ),
            log_output("FAILURE: \x1b[31mWA\x1b[39m"),
            log_output(
                "input:\n\x1b[1mabc\x1b[0m\x1b[2m\\n\x1b[0m",
            ),
            log_output("output:\n\x1b[1mABC\x1b[0m\x1b[2m\\n\x1b[0m"),
            log_output(
                "expected:\n\x1b[1mABC\x1b[0m\x1b[2m(no trailing newline)\x1b[0m",
            ),
        ],
    ),
    SingleCaseParams(
        name="check_output-AC",
        inbytes=b"abc\n",
        outbytes=b"ABC\n",
        mock_measure=OjExecInfo(
            answer=b"ABC\n", elapsed=1.25, memory=None, returncode=0
        ),
        expected={
            "name": "check_output-AC",
            "elapsed": 1.25,
            "exitcode": 0,
            "memory": None,
            "status": JudgeStatus.AC,
        },
        expected_log=[
            log_output("check_output-AC"),
            log_output("time: 1.250000 sec"),
            log_output("SUCCESS: \x1b[32mAC\x1b[39m"),
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
        expected={
            "name": "error-AC-equals",
            "elapsed": 1.25,
            "exitcode": 0,
            "memory": None,
            "status": JudgeStatus.AC,
        },
        expected_log=[
            log_output("error-AC-equals"),
            log_output("time: 1.250000 sec"),
            log_output("SUCCESS: \x1b[32mAC\x1b[39m"),
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
        expected={
            "name": "error-AC-long",
            "elapsed": 1.25,
            "exitcode": 0,
            "memory": None,
            "status": JudgeStatus.AC,
        },
        expected_log=[
            log_output("error-AC-long"),
            log_output("time: 1.250000 sec"),
            log_output("SUCCESS: \x1b[32mAC\x1b[39m"),
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
        expected={
            "name": "error-AC-short",
            "elapsed": 1.25,
            "exitcode": 0,
            "memory": None,
            "status": JudgeStatus.AC,
        },
        expected_log=[
            log_output("error-AC-short"),
            log_output("time: 1.250000 sec"),
            log_output("SUCCESS: \x1b[32mAC\x1b[39m"),
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
        expected={
            "name": "error-small-AC-abs",
            "elapsed": 1.25,
            "exitcode": 0,
            "memory": None,
            "status": JudgeStatus.AC,
        },
        expected_log=[
            log_output("error-small-AC-abs"),
            log_output("time: 1.250000 sec"),
            log_output("SUCCESS: \x1b[32mAC\x1b[39m"),
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
        expected={
            "name": "error-small-AC-abs-short",
            "elapsed": 1.25,
            "exitcode": 0,
            "memory": None,
            "status": JudgeStatus.AC,
        },
        expected_log=[
            log_output("error-small-AC-abs-short"),
            log_output("time: 1.250000 sec"),
            log_output("SUCCESS: \x1b[32mAC\x1b[39m"),
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
        expected={
            "name": "error-small-WA-abs",
            "elapsed": 1.25,
            "exitcode": 0,
            "memory": None,
            "status": JudgeStatus.WA,
        },
        expected_log=[
            log_output("error-small-WA-abs"),
            log_output("time: 1.250000 sec"),
            log_output("FAILURE: \x1b[31mWA\x1b[39m"),
            log_output(
                "input:\n"
                "\x1b[1mPlanck\x1b[0m\x1b[2m_\x1b[0m\x1b[1mmass\x1b[0m\x1b[2m\\n\x1b[0m",
            ),
            log_output(
                "output:\n\x1b[1m0.0000000217647\x1b[0m\x1b[2m\\n\x1b[0m",
            ),
            log_output(
                "expected:\n\x1b[1m0.0000000217640\x1b[0m\x1b[2m\\n\x1b[0m",
            ),
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
        expected={
            "name": "error-large-AC-rel",
            "elapsed": 1.25,
            "exitcode": 0,
            "memory": None,
            "status": JudgeStatus.AC,
        },
        expected_log=[
            log_output("error-large-AC-rel"),
            log_output("time: 1.250000 sec"),
            log_output("SUCCESS: \x1b[32mAC\x1b[39m"),
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
        expected={
            "name": "error-large-AC-rel-diff",
            "elapsed": 1.25,
            "exitcode": 0,
            "memory": None,
            "status": JudgeStatus.AC,
        },
        expected_log=[
            log_output("error-large-AC-rel-diff"),
            log_output("time: 1.250000 sec"),
            log_output("SUCCESS: \x1b[32mAC\x1b[39m"),
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
        expected={
            "name": "error-large-WA-rel",
            "elapsed": 1.25,
            "exitcode": 0,
            "memory": None,
            "status": JudgeStatus.WA,
        },
        expected_log=[
            log_output("error-large-WA-rel"),
            log_output("time: 1.250000 sec"),
            log_output("FAILURE: \x1b[31mWA\x1b[39m"),
            log_output(
                "input:\n"
                "\x1b[1mPlanck\x1b[0m\x1b[2m_\x1b[0m\x1b[1mtemp\x1b[0m\x1b[2m\\n\x1b[0m",
            ),
            log_output(
                "output:\n\x1b[1m141678400000021987654321987654321\x1b[0m\x1b[2m\\n\x1b[0m",
            ),
            log_output(
                "expected:\n\x1b[1m141678400000000000000000000000000\x1b[0m\x1b[2m\\n\x1b[0m",
            ),
        ],
    ),
    SingleCaseParams(
        name="lines-same",
        inbytes=b"abc\n",
        outbytes=b"ABC\nDEF\nGH\n",
        mock_measure=OjExecInfo(
            answer=b"ABC\nDEF\nGH\n", elapsed=1.25, memory=None, returncode=0
        ),
        expected={
            "name": "lines-same",
            "elapsed": 1.25,
            "exitcode": 0,
            "memory": None,
            "status": JudgeStatus.AC,
        },
        expected_log=[
            log_output("lines-same"),
            log_output("time: 1.250000 sec"),
            log_output("SUCCESS: \x1b[32mAC\x1b[39m"),
        ],
    ),
    SingleCaseParams(
        name="lines-crlf",
        inbytes=b"abc\n",
        outbytes=b"ABC\nDEF\nGH\n",
        mock_measure=OjExecInfo(
            answer=b"ABC\r\nDEF\r\nGH\r\n", elapsed=1.25, memory=None, returncode=0
        ),
        expected={
            "name": "lines-crlf",
            "elapsed": 1.25,
            "exitcode": 0,
            "memory": None,
            "status": JudgeStatus.AC,
        },
        expected_log=[
            log_output("lines-crlf"),
            log_output("time: 1.250000 sec"),
            log_output("SUCCESS: \x1b[32mAC\x1b[39m"),
        ],
    ),
    SingleCaseParams(
        name="lines-diff",
        inbytes=b"abc\n",
        outbytes=b"ABC\nDEF\nGH\n",
        mock_measure=OjExecInfo(
            answer=b"ABC\nDDF\nGH\n", elapsed=1.25, memory=None, returncode=0
        ),
        expected={
            "name": "lines-diff",
            "elapsed": 1.25,
            "exitcode": 0,
            "memory": None,
            "status": JudgeStatus.WA,
        },
        expected_log=[
            log_output("lines-diff"),
            log_output("time: 1.250000 sec"),
            log_output("FAILURE: \x1b[31mWA\x1b[39m"),
            log_output("input:\n\x1b[1mabc\x1b[0m\x1b[2m\\n\x1b[0m"),
            log_output(
                "output:\n"
                "\x1b[1mABC\x1b[0m\x1b[2m\\n\x1b[0m\x1b[1mDDF\x1b[0m\x1b[2m\\n\x1b[0m\x1b[1mGH\x1b[0m\x1b[2m\\n\x1b[0m",
            ),
            log_output(
                "expected:\n"
                "\x1b[1mABC\x1b[0m\x1b[2m\\n\x1b[0m\x1b[1mDEF\x1b[0m\x1b[2m\\n\x1b[0m\x1b[1mGH\x1b[0m\x1b[2m\\n\x1b[0m",
            ),
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
        expected={
            "name": "lines-error-diff-len",
            "elapsed": 1.25,
            "exitcode": 0,
            "memory": None,
            "status": JudgeStatus.AC,
        },
        expected_log=[
            log_output("lines-error-diff-len"),
            log_output("time: 1.250000 sec"),
            log_output("SUCCESS: \x1b[32mAC\x1b[39m"),
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
        expected={
            "name": "lines-error-grid",
            "elapsed": 1.25,
            "exitcode": 0,
            "memory": None,
            "status": JudgeStatus.AC,
        },
        expected_log=[
            log_output("lines-error-grid"),
            log_output("time: 1.250000 sec"),
            log_output("SUCCESS: \x1b[32mAC\x1b[39m"),
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
        expected={
            "name": "lines-grid-diff",
            "elapsed": 1.25,
            "exitcode": 0,
            "memory": None,
            "status": JudgeStatus.WA,
        },
        expected_log=[
            log_output("lines-grid-diff"),
            log_output("time: 1.250000 sec"),
            log_output("FAILURE: \x1b[31mWA\x1b[39m"),
            log_output("input:\n\x1b[1mabc\x1b[0m\x1b[2m\\n\x1b[0m"),
            log_output(
                "output:\n"
                "\x1b[1mABC\x1b[0m\x1b[2m_\x1b[0m\x1b[1mCD\x1b[0m\x1b[2m\\n"
                "\x1b[0m\x1b[1mDEF\x1b[0m\x1b[2m_\x1b[0m\x1b[1m3.14159265\x1b[0m\x1b[2m_\x1b[0m\x1b[1m3.14\x1b[0m\x1b[2m\\n"
                "\x1b[0m\x1b[1m3.14159265\x1b[0m\x1b[2m\\n\x1b[0m",
            ),
            log_output(
                "expected:\n"
                "\x1b[1mABC\x1b[0m\x1b[2m_\x1b[0m\x1b[1mCD\x1b[0m\x1b[2m\\n"
                "\x1b[0m\x1b[1mDEF\x1b[0m\x1b[2m_\x1b[0m\x1b[1m3.141592653589\x1b[0m\x1b[2m\\n"
                "\x1b[0m\x1b[1m3.14159265358979\x1b[0m\x1b[2m\\n\x1b[0m",
            ),
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
        expected={
            "name": "lines-grid-diff-lines",
            "elapsed": 1.25,
            "exitcode": 0,
            "memory": None,
            "status": JudgeStatus.WA,
        },
        expected_log=[
            log_output("lines-grid-diff-lines"),
            log_output("time: 1.250000 sec"),
            log_output("FAILURE: \x1b[31mWA\x1b[39m"),
            log_output("input:\n\x1b[1mabc\x1b[0m\x1b[2m\\n\x1b[0m"),
            log_output(
                "output:\n"
                "\x1b[1mABC\x1b[0m\x1b[2m_\x1b[0m\x1b[1mCD\x1b[0m\x1b[2m\\n"
                "\x1b[0m\x1b[1mDEF\x1b[0m\x1b[2m_\x1b[0m\x1b[1m3.14159265\x1b[0m\x1b[2m_\x1b[0m\x1b[1m3.14\x1b[0m\x1b[2m\\n"
                "\x1b[0m\x1b[1m3.14159265\x1b[0m\x1b[2m\\n\x1b[0m\x1b[1mno\x1b[0m\x1b[2m\\n\x1b[0m",
            ),
            log_output(
                "expected:\n"
                "\x1b[1mABC\x1b[0m\x1b[2m_\x1b[0m\x1b[1mCD\x1b[0m\x1b[2m\\n"
                "\x1b[0m\x1b[1mDEF\x1b[0m\x1b[2m_\x1b[0m\x1b[1m3.141592653589\x1b[0m\x1b[2m\\n"
                "\x1b[0m\x1b[1m3.14159265358979\x1b[0m\x1b[2m\\n\x1b[0m",
            ),
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
        expected={
            "name": "error-str-same",
            "elapsed": 1.25,
            "exitcode": 0,
            "memory": None,
            "status": JudgeStatus.AC,
        },
        expected_log=[
            log_output("error-str-same"),
            log_output("time: 1.250000 sec"),
            log_output("SUCCESS: \x1b[32mAC\x1b[39m"),
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
        expected={
            "name": "error-str-WA",
            "elapsed": 1.25,
            "exitcode": 0,
            "memory": None,
            "status": JudgeStatus.WA,
        },
        expected_log=[
            log_output("error-str-WA"),
            log_output("time: 1.250000 sec"),
            log_output("FAILURE: \x1b[31mWA\x1b[39m"),
            log_output("input:\n\x1b[1mabc\x1b[0m\x1b[2m\\n\x1b[0m"),
            log_output("output:\n\x1b[1mABC\x1b[0m\x1b[2m\\n\x1b[0m"),
            log_output("expected:\n\x1b[1mDEF\x1b[0m\x1b[2m\\n\x1b[0m"),
        ],
    ),
    SingleCaseParams(
        name="TLE",
        inbytes=b"abc\n",
        outbytes=b"ABC\n",
        mock_measure=OjExecInfo(
            answer=b"ABC\n", elapsed=1.25, memory=None, returncode=None
        ),
        expected={
            "name": "TLE",
            "elapsed": 1.25,
            "exitcode": None,
            "memory": None,
            "status": JudgeStatus.TLE,
        },
        expected_log=[
            log_output("TLE"),
            log_output("time: 1.250000 sec"),
            log_output("FAILURE: \x1b[31mTLE\x1b[39m"),
            log_output(
                "input:\n\x1b[1mabc\x1b[0m\x1b[2m\\n\x1b[0m",
            ),
        ],
    ),
    SingleCaseParams(
        name="RE",
        inbytes=b"abc\n",
        outbytes=b"ABC\n",
        mock_measure=OjExecInfo(
            answer=b"ABC\n", elapsed=1.25, memory=None, returncode=1
        ),
        expected={
            "name": "RE",
            "elapsed": 1.25,
            "exitcode": 1,
            "memory": None,
            "status": JudgeStatus.RE,
        },
        expected_log=[
            log_output("RE"),
            log_output("time: 1.250000 sec"),
            log_output("FAILURE: \x1b[31mRE\x1b[39m: return code 1"),
            log_output(
                "input:\n\x1b[1mabc\x1b[0m\x1b[2m\\n\x1b[0m",
            ),
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
        expected={
            "name": "MLE-NotMeasure",
            "elapsed": 1.25,
            "exitcode": 0,
            "memory": None,
            "status": JudgeStatus.AC,
        },
        expected_log=[
            log_output("MLE-NotMeasure"),
            log_output("time: 1.250000 sec"),
            log_output("SUCCESS: \x1b[32mAC\x1b[39m"),
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
        expected={
            "name": "MLE-Safe",
            "elapsed": 1.25,
            "exitcode": 0,
            "memory": 128,
            "status": JudgeStatus.AC,
        },
        expected_log=[
            log_output("MLE-Safe"),
            log_output("time: 1.250000 sec, memory: 128.000000 MB"),
            log_output("SUCCESS: \x1b[32mAC\x1b[39m"),
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
        expected={
            "name": "MLE",
            "elapsed": 1.25,
            "exitcode": 1,
            "memory": 128.1,
            "status": JudgeStatus.MLE,
        },
        expected_log=[
            log_output("MLE"),
            log_output("time: 1.250000 sec, memory: 128.100000 MB"),
            log_output("FAILURE: \x1b[31mMLE\x1b[39m"),
            log_output(
                "input:\n\x1b[1mabc\x1b[0m\x1b[2m\\n\x1b[0m",
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
        expected={
            "name": "unicode-error",
            "elapsed": 1.25,
            "exitcode": 0,
            "memory": None,
            "status": JudgeStatus.WA,
        },
        expected_log=[
            log_output("unicode-error"),
            log_output("time: 1.250000 sec"),
            log_output("FAILURE: \x1b[31mWA\x1b[39m"),
            log_output("input:\n\x1b[1ma\x1b[0m\x1b[2m\\n\x1b[0m"),
            log_output(
                "output:\n"
                "\x1b[2m'utf-8' codec can't decode byte 0x82 in position 0: invalid "
                "start byte\x1b[0m\x1b[1m\ufffd\ufffd\x1b[0m\x1b[2m\\n\x1b[0m"
            ),
            log_output("expected:\n\x1b[1mA\x1b[0m\x1b[2m\\n\x1b[0m"),
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
        expected={
            "name": "long-lines",
            "elapsed": 1.25,
            "exitcode": 0,
            "memory": None,
            "status": JudgeStatus.WA,
        },
        expected_log=[
            log_output("long-lines"),
            log_output("time: 1.250000 sec"),
            log_output("FAILURE: \x1b[31mWA\x1b[39m"),
            log_output("input:\n\x1b[1mabc\x1b[0m\x1b[2m\\n\x1b[0m"),
            log_output(
                "output:\n"
                "\x1b[1mea226088-3cc7-4d33-9\x1b[0m\x1b[2m... (145 chars) "
                "...\x1b[0m\x1b[1md-9f86-b0bba61f2608\x1b[0m\x1b[2m\\n\x1b[0m",
            ),
            log_output("expected:\n\x1b[1mABC\x1b[0m\x1b[2m\\n\x1b[0m"),
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
        expected={
            "name": "long-text",
            "elapsed": 1.25,
            "exitcode": 0,
            "memory": None,
            "status": JudgeStatus.WA,
        },
        expected_log=[
            log_output("long-text"),
            log_output("time: 1.250000 sec"),
            log_output("FAILURE: \x1b[31mWA\x1b[39m"),
            log_output(
                "input:\n\x1b[1mabc\x1b[0m\x1b[2m\\n\x1b[0m",
            ),
            log_output(
                "output:\n"
                "\x1b[1mea226088-3cc7-4d33-9\x1b[0m\x1b[2m... (178 chars) ...\x1b[0m"
                "\x1b[1m-bb82-ae4591ed8ccd\x1b[0m\x1b[2m\\r\\n\x1b[0m",
            ),
            log_output("expected:\n\x1b[1mABC\x1b[0m\x1b[2m\\n\x1b[0m"),
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
        expected={
            "name": "long-lines-break",
            "elapsed": 1.25,
            "exitcode": 0,
            "memory": None,
            "status": JudgeStatus.WA,
        },
        expected_log=[
            log_output("long-lines-break"),
            log_output("time: 1.250000 sec"),
            log_output("FAILURE: \x1b[31mWA\x1b[39m"),
            log_output("input:\n\x1b[1mabc\x1b[0m\x1b[2m\\n\x1b[0m"),
            log_output(
                "output:\n"
                "\x1b[1mea226088-3cc7-4d33-\x1b[0m\x1b[2m\\n\x1b[0m\x1b[2m... (147 chars) "
                "...\x1b[0m\x1b[2m\\n\x1b[0m\x1b[1m-9f86-b0bba61f2608\x1b[0m\x1b[2m\\n\x1b[0m",
            ),
            log_output("expected:\n\x1b[1mABC\x1b[0m\x1b[2m\\n\x1b[0m"),
        ],
    ),
]


@pytest.mark.usefixtures("mock_measure", "mock_terminal_size")
@pytest.mark.parametrize(
    (
        "name",
        "inbytes",
        "mock_measure",
        "expected",
        "expected_log",
        "outbytes",
        "error",
        "mle",
        "mock_judge",
    ),
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
    expected: dict[str, Any],
    expected_log: list[tuple[str, int, str]],
    caplog: pytest.LogCaptureFixture,
    mock_judge: bool,
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
            directory=testtemp,
            error=error,
            mle=mle,
            judge=pathlib.Path("echo 1") if mock_judge else None,
            tle=None,
        ),
    )

    expected["input"] = input_path
    expected["output"] = output_path
    assert result.model_dump() == expected
    assert caplog.record_tuples == expected_log
