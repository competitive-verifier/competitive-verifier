# flake8: noqa E501
import pathlib
import sys
from dataclasses import dataclass
from typing import Any, Optional, Sequence

import pytest
from pydantic import RootModel
from pytest_mock import MockerFixture
from pytest_mock.plugin import MockType

import competitive_verifier.models
from competitive_verifier.models import (
    CommandVerification,
    ConstVerification,
    ProblemVerification,
    ResultStatus,
    Verification,
)


@dataclass
class DataVerificationParams:
    default_tle: float
    default_mle: float


test_command_union_json_params: list[tuple[Verification, str, str]] = [
    (
        ConstVerification(status=ResultStatus.SUCCESS),
        '{"type": "const","status":"success"}',
        '{"type":"const","status":"success"}',
    ),
    (
        ConstVerification(status=ResultStatus.SUCCESS, name="foo"),
        '{"type": "const","name":"foo","status":"success"}',
        '{"name":"foo","type":"const","status":"success"}',
    ),
    (
        ConstVerification(status=ResultStatus.FAILURE),
        '{"type": "const","status":"failure"}',
        '{"type":"const","status":"failure"}',
    ),
    (
        ConstVerification(status=ResultStatus.SKIPPED),
        '{"type": "const","status":"skipped"}',
        '{"type":"const","status":"skipped"}',
    ),
    (
        ConstVerification(status=ResultStatus.SUCCESS),
        '{"type": "const","status":"success"}',
        '{"type":"const","status":"success"}',
    ),
    (
        CommandVerification(command="ls ~"),
        '{"type":"command","command":"ls ~"}',
        '{"type":"command","command":"ls ~"}',
    ),
    (
        CommandVerification(compile="cat LICENSE", command="ls ~"),
        '{"type": "command", "compile": "cat LICENSE", "command": "ls ~"}',
        '{"type":"command","command":"ls ~","compile":"cat LICENSE"}',
    ),
    (
        ProblemVerification(command="ls ~", problem="https://example.com"),
        '{"type":"problem","problem":"https://example.com","command":"ls ~"}',
        '{"type":"problem","command":"ls ~","problem":"https://example.com"}',
    ),
    (
        ProblemVerification(name="bar", command="ls ~", problem="https://example.com"),
        '{"type":"problem","name":"bar","problem":"https://example.com","command":"ls ~"}',
        '{"name":"bar","type":"problem","command":"ls ~","problem":"https://example.com"}',
    ),
    (
        ProblemVerification(
            compile="cat LICENSE", command="ls ~", problem="https://example.com"
        ),
        '{"type": "problem",  "problem":"https://example.com", "compile": "cat LICENSE", "command": "ls ~"}',
        '{"type":"problem","command":"ls ~","compile":"cat LICENSE","problem":"https://example.com"}',
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
        '{"type":"problem","command":"ls ~","compile":"cat LICENSE","problem":"https://example.com","error":1e-6,"tle":2.0}',
    ),
]


@pytest.mark.parametrize("obj, raw_json, output_json", test_command_union_json_params)
def test_command_union_json(
    obj: Verification,
    raw_json: str,
    output_json: str,
):
    VerificationUnion = RootModel[Verification]

    assert obj == type(obj).model_validate_json(raw_json)
    assert obj.model_dump_json(exclude_none=True) == output_json

    assert obj == VerificationUnion.model_validate_json(raw_json).root


def test_const_verification(mock_exec_command: MockType):
    obj = ConstVerification(status=ResultStatus.SUCCESS)

    assert obj.run() == ResultStatus.SUCCESS
    assert obj.run_compile_command()
    mock_exec_command.assert_not_called()


test_run_params: list[tuple[Verification, Sequence[str], dict[str, Any]]] = [
    (
        CommandVerification(command="ls ~"),
        ("ls ~",),
        {
            "shell": True,
            "text": True,
            "check": False,
            "env": None,
            "capture_output": False,
            "encoding": sys.stdout.encoding,
        },
    ),
    (
        CommandVerification(compile="cat LICENSE", command="ls ~"),
        ("ls ~",),
        {
            "shell": True,
            "text": True,
            "check": False,
            "env": None,
            "capture_output": False,
            "encoding": sys.stdout.encoding,
        },
    ),
]


@pytest.mark.parametrize("obj, args, kwargs", test_run_params)
def test_run(
    obj: Verification,
    args: Sequence[Any],
    kwargs: dict[str, Any],
    mock_exec_command: MockType,
    mocker: MockerFixture,
):
    mocker.patch(
        "onlinejudge._implementation.utils.user_cache_dir", pathlib.Path("/bar/baz")
    )
    obj.run(
        DataVerificationParams(
            default_tle=22,
            default_mle=128,
        ),
    )
    mock_exec_command.assert_called_once_with(*args, **kwargs)


test_run_problem_command_params: list[tuple[ProblemVerification, dict[str, Any]]] = [
    (
        ProblemVerification(command="ls ~", problem="https://example.com"),
        {
            "url": "https://example.com",
            "command": "ls ~",
            "tle": 22.0,
            "error": None,
            "mle": 128,
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
            "mle": 128,
        },
    ),
    (
        ProblemVerification(
            compile="cat LICENSE",
            command="ls ~",
            problem="https://example.com",
            error=1e-6,
            tle=2,
            mle=1.2,
        ),
        {
            "url": "https://example.com",
            "command": "ls ~",
            "tle": 2.0,
            "error": 1e-06,
            "mle": 1.2,
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
            "mle": 128,
        },
    ),
]


@pytest.mark.parametrize("obj, kwargs", test_run_problem_command_params)
def test_run_problem_command(
    obj: ProblemVerification,
    kwargs: dict[str, Any],
    mocker: MockerFixture,
):
    patch = mocker.patch.object(competitive_verifier.models.verification.oj, "test")
    obj.run(
        DataVerificationParams(default_tle=22, default_mle=128),
    )
    patch.assert_called_once_with(**kwargs)


test_run_compile_params: list[
    tuple[Verification, Optional[Sequence[str]], Optional[dict[str, Any]]]
] = [
    (
        CommandVerification(command="ls ~"),
        None,
        None,
    ),
    (
        CommandVerification(compile="cat LICENSE", command="ls ~"),
        ("cat LICENSE",),
        {
            "shell": True,
            "text": True,
            "check": False,
            "env": None,
            "capture_output": False,
            "encoding": sys.stdout.encoding,
        },
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
        {
            "shell": True,
            "text": True,
            "check": False,
            "env": None,
            "capture_output": False,
            "encoding": sys.stdout.encoding,
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
        ("cat LICENSE",),
        {
            "shell": True,
            "text": True,
            "check": False,
            "env": None,
            "capture_output": False,
            "encoding": sys.stdout.encoding,
        },
    ),
]


@pytest.mark.parametrize("obj, args, kwargs", test_run_compile_params)
def test_run_compile(
    obj: Verification,
    args: Optional[Sequence[Any]],
    kwargs: Optional[dict[str, Any]],
    mock_exec_command: MockType,
):
    obj.run_compile_command(
        DataVerificationParams(
            default_tle=22,
            default_mle=128,
        ),
    )
    if args is None:
        mock_exec_command.assert_not_called()
    else:
        assert kwargs
        mock_exec_command.assert_called_once_with(*args, **kwargs)


test_params_run_params: list[tuple[Verification, Optional[str]]] = [
    (ConstVerification(status=ResultStatus.SUCCESS), None),
    (CommandVerification(command="true"), None),
    (
        ProblemVerification(command="true", problem="http://example.com"),
        "ProblemVerification.run requires VerificationParams",
    ),
]


@pytest.mark.parametrize("obj, error_message", test_params_run_params)
def test_params_run(
    obj: Verification,
    error_message: Optional[str],
    mock_exec_command: MockType,
):
    if error_message:
        with pytest.raises(ValueError) as e:
            obj.run()
        assert e.value.args == (error_message,)
    else:
        obj.run()
