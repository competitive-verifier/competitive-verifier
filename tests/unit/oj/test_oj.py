from typing import Any

import pytest
from pytest_mock import MockerFixture

from competitive_verifier import oj
from competitive_verifier.oj.oj_test import OjTestArguments
from competitive_verifier.oj.problem import LibraryCheckerProblem, YukicoderProblem

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
