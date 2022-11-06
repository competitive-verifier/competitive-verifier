# flake8: noqa E501
import pathlib
from dataclasses import dataclass
from typing import Any, Sequence
from unittest import mock

import pytest
from pydantic import BaseModel

import competitive_verifier.models
from competitive_verifier.models import (
    Command,
    DummyCommand,
    ProblemVerificationCommand,
    VerificationCommand,
)


@dataclass
class DataVerificationParams:
    default_tle: float


command_union_json_params = [  # type: ignore
    (DummyCommand(), '{"type": "dummy"}', '{"type": "dummy"}'),
    (
        VerificationCommand(command="ls ~"),
        '{"type":"command","command":"ls ~"}',
        '{"type": "command", "command": "ls ~", "compile": null}',
    ),
    (
        VerificationCommand(compile="cat LICENSE", command="ls ~"),
        '{"type": "command", "compile": "cat LICENSE", "command": "ls ~"}',
        '{"type": "command", "command": "ls ~", "compile": "cat LICENSE"}',
    ),
    (
        ProblemVerificationCommand(command="ls ~", problem="https://example.com"),
        '{"type":"problem","problem":"https://example.com","command":"ls ~"}',
        '{"type": "problem", "command": "ls ~", "compile": null, "problem": "https://example.com", "error": null, "tle": null}',
    ),
    (
        ProblemVerificationCommand(
            compile="cat LICENSE", command="ls ~", problem="https://example.com"
        ),
        '{"type": "problem",  "problem":"https://example.com", "compile": "cat LICENSE", "command": "ls ~"}',
        '{"type": "problem", "command": "ls ~", "compile": "cat LICENSE", "problem": "https://example.com", "error": null, "tle": null}',
    ),
    (
        ProblemVerificationCommand(
            compile="cat LICENSE",
            command="ls ~",
            problem="https://example.com",
            error=1e-6,
            tle=2,
        ),
        '{"type": "problem",  "problem":"https://example.com", "compile": "cat LICENSE", "error": 0.000001, "tle": 2, "command": "ls ~"}',
        '{"type": "problem", "command": "ls ~", "compile": "cat LICENSE", "problem": "https://example.com", "error": 1e-06, "tle": 2.0}',
    ),
]


@pytest.mark.parametrize("obj, raw_json, output_json", command_union_json_params)
def test_command_union_json(
    obj: Command,
    raw_json: str,
    output_json: str,
):
    class CommandUnion(BaseModel):
        __root__: Command

    assert obj == type(obj).parse_raw(raw_json)
    assert obj.json() == output_json

    assert obj == CommandUnion.parse_raw(raw_json).__root__


command_command_params = [  # type: ignore
    (DummyCommand(), None, None),
    (VerificationCommand(command="ls ~"), "ls ~", None),
    (
        VerificationCommand(compile="cat LICENSE", command="ls ~"),
        "ls ~",
        "cat LICENSE",
    ),
    (
        ProblemVerificationCommand(command="ls ~", problem="https://example.com"),
        "ls ~",
        None,
    ),
    (
        ProblemVerificationCommand(
            compile="cat LICENSE", command="ls ~", problem="https://example.com"
        ),
        "ls ~",
        "cat LICENSE",
    ),
    (
        ProblemVerificationCommand(
            compile="cat LICENSE",
            command="ls ~",
            problem="https://example.com",
            error=1e-6,
            tle=2,
        ),
        "ls ~",
        "cat LICENSE",
    ),
]


def mock_exec_command():
    return mock.patch.object(competitive_verifier.models.command.exec, "exec_command")


def test_dummy():
    obj = DummyCommand()
    with mock_exec_command() as patch:
        obj.run_command()
        obj.run_compile_command()
        patch.assert_not_called()


run_command_params = [  # type: ignore
    (VerificationCommand(command="ls ~"), ("ls ~",), {"text": True}),
    (
        VerificationCommand(compile="cat LICENSE", command="ls ~"),
        ("ls ~",),
        {"text": True},
    ),
]


@pytest.mark.parametrize("obj, args, kwargs", run_command_params)
def test_run_command(obj: Command, args: Sequence[Any], kwargs: dict[str, Any]):
    with mock.patch(
        "onlinejudge._implementation.utils.user_cache_dir", pathlib.Path("/bar/baz")
    ), mock_exec_command() as patch:
        obj.run_command(
            DataVerificationParams(
                default_tle=22,
            ),
        )
        patch.assert_called_once_with(*args, **kwargs)


run_problem_command_params: list[tuple[ProblemVerificationCommand, dict[str, Any]]] = [
    (
        ProblemVerificationCommand(command="ls ~", problem="https://example.com"),
        {
            "url": "https://example.com",
            "command": "ls ~",
            "tle": 22.0,
            "error": None,
        },
    ),
    (
        ProblemVerificationCommand(
            compile="cat LICENSE", command="ls ~", problem="https://example.com"
        ),
        {
            "url": "https://example.com",
            "command": "ls ~",
            "tle": 22.0,
            "error": None,
        },
    ),
    (
        ProblemVerificationCommand(
            compile="cat LICENSE",
            command="ls ~",
            problem="https://example.com",
            error=1e-6,
            tle=2,
        ),
        {
            "url": "https://example.com",
            "command": "ls ~",
            "tle": 2.0,
            "error": 1e-06,
        },
    ),
    (
        ProblemVerificationCommand(
            compile="cat LICENSE",
            command="ls ~",
            problem="https://judge.yosupo.jp/problem/aplusb",
            error=1e-6,
            tle=2,
        ),
        {
            "url": "https://judge.yosupo.jp/problem/aplusb",
            "command": "ls ~",
            "tle": 2.0,
            "error": 1e-06,
        },
    ),
]


@pytest.mark.parametrize("obj, kwargs", run_problem_command_params)
def test_run_problem_command(obj: ProblemVerificationCommand, kwargs: dict[str, Any]):
    with mock.patch.object(competitive_verifier.models.command.oj, "test") as patch:
        obj.run_command(
            DataVerificationParams(default_tle=22),
        )
        patch.assert_called_once_with(**kwargs)


run_compile_params = [  # type: ignore
    (
        VerificationCommand(command="ls ~"),
        None,
        None,
    ),
    (
        VerificationCommand(compile="cat LICENSE", command="ls ~"),
        ("cat LICENSE",),
        {"text": True},
    ),
    (
        ProblemVerificationCommand(command="ls ~", problem="https://example.com"),
        None,
        None,
    ),
    (
        ProblemVerificationCommand(
            compile="cat LICENSE", command="ls ~", problem="https://example.com"
        ),
        ("cat LICENSE",),
        {"text": True},
    ),
    (
        ProblemVerificationCommand(
            compile="cat LICENSE",
            command="ls ~",
            problem="https://example.com",
            error=1e-6,
            tle=2,
        ),
        ("cat LICENSE",),
        {"text": True},
    ),
]


@pytest.mark.parametrize("obj, args, kwargs", run_compile_params)
def test_run_compile(obj: Command, args: Sequence[Any], kwargs: dict[str, Any]):
    with mock_exec_command() as patch:
        obj.run_compile_command(
            DataVerificationParams(
                default_tle=22,
            ),
        )
        if args is None:
            patch.assert_not_called()
        else:
            patch.assert_called_once_with(*args, **kwargs)


params_run_command_params = [  # type: ignore
    (DummyCommand(), None),
    (VerificationCommand(command="true"), None),
    (
        ProblemVerificationCommand(command="true", problem="http://example.com"),
        "ProblemVerificationCommand.run_command requires VerificationParams",
    ),
]


@pytest.mark.parametrize("obj, error_message", params_run_command_params)
def test_params_run_command(obj: Command, error_message: str):
    with mock_exec_command():
        if error_message:
            with pytest.raises(ValueError) as e:
                obj.run_command()
            assert e.value.args == (error_message,)
        else:
            obj.run_command()
