import pathlib
from typing import Any

import pytest
from pytest_mock import MockerFixture

import competitive_verifier.oj as oj
from competitive_verifier.oj.tools.test_command import OjTestArguments

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
            cookie=pathlib.Path("/bar/baz/online-judge-tools") / "cookie.txt",
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
            cookie=pathlib.Path("/bar/baz/online-judge-tools") / "cookie.txt",
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
    "input, expected",
    test_oj_test_params.values(),
    ids=test_oj_test_params.keys(),
)
def test_oj_test(
    mocker: MockerFixture,
    input: dict[str, Any],
    expected: OjTestArguments,
):
    mocker.patch(
        "competitive_verifier.oj.tools.test_command.get_cache_directory",
        return_value=pathlib.Path("/bar/baz/online-judge-tools"),
    )
    run = mocker.patch("competitive_verifier.oj.tools.test_command.run")

    oj.test(**input)

    run.assert_called_once_with(expected)
