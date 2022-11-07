# flake8: noqa E501
import pathlib
from dataclasses import dataclass
from typing import Any, Sequence
from unittest import mock

import pytest
from pydantic import BaseModel

import competitive_verifier.models
from competitive_verifier.models import (
    CommandVerification,
    DependencyVerification,
    ProblemVerification,
    Verification,
)


@dataclass
class DataVerificationParams:
    default_tle: float


test_command_union_json_params = [  # type: ignore
    (
        DependencyVerification(dependency=pathlib.Path("foo/bar.py")),
        '{"type": "dependency","dependency":"foo/bar.py"}',
        '{"type": "dependency", "dependency": "foo/bar.py"}',
    ),
    (
        CommandVerification(command="ls ~"),
        '{"type":"command","command":"ls ~"}',
        '{"type": "command", "command": "ls ~", "compile": null}',
    ),
    (
        CommandVerification(compile="cat LICENSE", command="ls ~"),
        '{"type": "command", "compile": "cat LICENSE", "command": "ls ~"}',
        '{"type": "command", "command": "ls ~", "compile": "cat LICENSE"}',
    ),
    (
        ProblemVerification(command="ls ~", problem="https://example.com"),
        '{"type":"problem","problem":"https://example.com","command":"ls ~"}',
        '{"type": "problem", "command": "ls ~", "compile": null, "problem": "https://example.com", "error": null, "tle": null}',
    ),
    (
        ProblemVerification(
            compile="cat LICENSE", command="ls ~", problem="https://example.com"
        ),
        '{"type": "problem",  "problem":"https://example.com", "compile": "cat LICENSE", "command": "ls ~"}',
        '{"type": "problem", "command": "ls ~", "compile": "cat LICENSE", "problem": "https://example.com", "error": null, "tle": null}',
    ),
    (
        ProblemVerification(
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


@pytest.mark.parametrize("obj, raw_json, output_json", test_command_union_json_params)
def test_command_union_json(
    obj: Verification,
    raw_json: str,
    output_json: str,
):
    class VerificationUnion(BaseModel):
        __root__: Verification

    assert obj == type(obj).parse_raw(raw_json)
    assert obj.json() == output_json

    assert obj == VerificationUnion.parse_raw(raw_json).__root__


def mock_exec_command():
    return mock.patch.object(
        competitive_verifier.models.verification.exec, "exec_command"
    )


def test_dendency_verification():
    obj = DependencyVerification(dependency=pathlib.Path("."))
    with mock_exec_command() as patch:
        obj.run_command()
        obj.run_compile_command()
        patch.assert_not_called()


test_run_command_params = [  # type: ignore
    (CommandVerification(command="ls ~"), ("ls ~",), {"text": True}),
    (
        CommandVerification(compile="cat LICENSE", command="ls ~"),
        ("ls ~",),
        {"text": True},
    ),
]


@pytest.mark.parametrize("obj, args, kwargs", test_run_command_params)
def test_run_command(obj: Verification, args: Sequence[Any], kwargs: dict[str, Any]):
    with mock.patch(
        "onlinejudge._implementation.utils.user_cache_dir", pathlib.Path("/bar/baz")
    ), mock_exec_command() as patch:
        obj.run_command(
            DataVerificationParams(
                default_tle=22,
            ),
        )
        patch.assert_called_once_with(*args, **kwargs)


test_run_problem_command_params: list[tuple[ProblemVerification, dict[str, Any]]] = [
    (
        ProblemVerification(command="ls ~", problem="https://example.com"),
        {
            "url": "https://example.com",
            "command": "ls ~",
            "tle": 22.0,
            "error": None,
        },
    ),
    (
        ProblemVerification(
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
        ProblemVerification(
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
        ProblemVerification(
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


@pytest.mark.parametrize("obj, kwargs", test_run_problem_command_params)
def test_run_problem_command(obj: ProblemVerification, kwargs: dict[str, Any]):
    with mock.patch.object(
        competitive_verifier.models.verification.oj, "test"
    ) as patch:
        obj.run_command(
            DataVerificationParams(default_tle=22),
        )
        patch.assert_called_once_with(**kwargs)


test_run_compile_params = [  # type: ignore
    (
        CommandVerification(command="ls ~"),
        None,
        None,
    ),
    (
        CommandVerification(compile="cat LICENSE", command="ls ~"),
        ("cat LICENSE",),
        {"text": True},
    ),
    (
        ProblemVerification(command="ls ~", problem="https://example.com"),
        None,
        None,
    ),
    (
        ProblemVerification(
            compile="cat LICENSE", command="ls ~", problem="https://example.com"
        ),
        ("cat LICENSE",),
        {"text": True},
    ),
    (
        ProblemVerification(
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


@pytest.mark.parametrize("obj, args, kwargs", test_run_compile_params)
def test_run_compile(obj: Verification, args: Sequence[Any], kwargs: dict[str, Any]):
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


test_params_run_command_params = [  # type: ignore
    (DependencyVerification(dependency=pathlib.Path("foo/bar.py")), None),
    (CommandVerification(command="true"), None),
    (
        ProblemVerification(command="true", problem="http://example.com"),
        "ProblemVerification.run_command requires VerificationParams",
    ),
]


@pytest.mark.parametrize("obj, error_message", test_params_run_command_params)
def test_params_run_command(obj: Verification, error_message: str):
    with mock_exec_command():
        if error_message:
            with pytest.raises(ValueError) as e:
                obj.run_command()
            assert e.value.args == (error_message,)
        else:
            obj.run_command()
