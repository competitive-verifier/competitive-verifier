import pathlib
from typing import Any

import pytest
from pytest_mock import MockerFixture

from competitive_verifier import oj
from competitive_verifier.oj.tools.oj_test import OjTestArguments
from competitive_verifier.oj.tools.problem import (
    LibraryCheckerProblem,
    YukicoderProblem,
)

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
            directory=pathlib.Path(
                ".competitive-verifier/cache/problems/f8e4a4fdd296c1bdd2cc4f91475a6204/test"
            ),
            judge=pathlib.Path(
                ".competitive-verifier/cache/problems/f8e4a4fdd296c1bdd2cc4f91475a6204/mockcheck"
            ),
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
            directory=pathlib.Path(
                ".competitive-verifier/cache/problems/83bab2909b81aa308aac28580826a6d9/test"
            ),
            judge=None,
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
        "competitive_verifier.oj.tools.problem.LibraryCheckerProblem.checker_exe_name",
        "mockcheck",
    )
    run = mocker.patch("competitive_verifier.oj.tools.oj_test._run")

    oj.test(**args)

    run.assert_called_once_with(expected)
