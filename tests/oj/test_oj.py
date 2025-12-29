import pathlib
from typing import Any

import pytest
from pytest_mock import MockerFixture

from competitive_verifier import oj
from competitive_verifier.oj.tools.oj_test import OjTestArguments

test_oj_test_params: dict[str, tuple[dict[str, Any], OjTestArguments]] = {
    "default": (
        {
            "url": "http://example.com",
            "command": "ls .",
            "tle": 2,
            "error": None,
            "mle": 128,
            "env": None,
        },
        OjTestArguments(
            command="ls .",
            tle=2,
            print_input=True,
            mle=128,
            error=None,
            directory=pathlib.Path(
                ".competitive-verifier/cache/problems/a9b9f04336ce0181a08e774e01113b31/test"
            ),
            judge=None,
        ),
    ),
    "with_env": (
        {
            "url": "http://example.com",
            "command": ["ls", "."],
            "tle": 30,
            "error": None,
            "mle": 256,
            "env": {"TOKEN": "Dummy"},
        },
        OjTestArguments(
            command=["ls", "."],
            tle=30,
            print_input=True,
            mle=256,
            error=None,
            directory=pathlib.Path(
                ".competitive-verifier/cache/problems/a9b9f04336ce0181a08e774e01113b31/test"
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
    run = mocker.patch("competitive_verifier.oj.tools.oj_test.run")

    oj.test(**args)

    run.assert_called_once_with(expected)
