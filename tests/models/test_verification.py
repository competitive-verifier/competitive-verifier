# flake8: noqa E501
import pathlib
import sys
from dataclasses import dataclass
from typing import Any, Optional, Sequence, Union

import pytest
from pydantic import RootModel
from pytest_mock import MockerFixture
from pytest_mock.plugin import MockType

import competitive_verifier.models
import competitive_verifier.oj.tools.test_command
from competitive_verifier.models import (
    CommandVerification,
    ConstVerification,
    ProblemVerification,
    ResultStatus,
    ShellCommand,
    Verification,
)
from competitive_verifier.oj.tools.test_command import OjTestArguments


@dataclass
class DataVerificationParams:
    default_tle: Optional[float]
    default_mle: Optional[float]


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


test_run_params: list[
    tuple[Verification, tuple[Union[str, list[str]]], dict[str, Any]]
] = [
    (
        CommandVerification(command="ls ~"),
        ("ls ~",),
        {
            "shell": True,
            "text": True,
            "check": False,
            "cwd": None,
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
            "cwd": None,
            "env": None,
            "capture_output": False,
            "encoding": sys.stdout.encoding,
        },
    ),
    (
        CommandVerification(command=["ls", "~"]),
        (["ls", "~"],),
        {
            "shell": False,
            "text": True,
            "check": False,
            "cwd": None,
            "env": None,
            "capture_output": False,
            "encoding": sys.stdout.encoding,
        },
    ),
    (
        CommandVerification(command=["ls", "~"]),
        (["ls", "~"],),
        {
            "shell": False,
            "text": True,
            "check": False,
            "cwd": None,
            "env": None,
            "capture_output": False,
            "encoding": sys.stdout.encoding,
        },
    ),
    (
        CommandVerification(
            command=ShellCommand(command="ls ~", cwd=pathlib.Path("/foo")),
        ),
        ("ls ~",),
        {
            "shell": True,
            "text": True,
            "check": False,
            "cwd": pathlib.Path("/foo"),
            "env": None,
            "capture_output": False,
            "encoding": sys.stdout.encoding,
        },
    ),
    (
        CommandVerification(
            command=ShellCommand(command=["ls", "~"], cwd=pathlib.Path("~")),
        ),
        (["ls", "~"],),
        {
            "shell": False,
            "text": True,
            "check": False,
            "cwd": pathlib.Path("~"),
            "env": None,
            "capture_output": False,
            "encoding": sys.stdout.encoding,
        },
    ),
]


@pytest.mark.parametrize(
    "obj, args, kwargs",
    test_run_params,
    ids=range(len(test_run_params)),
)
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


test_run_with_env_params: list[
    tuple[Verification, tuple[Union[str, list[str]]], dict[str, Any], dict[str, str]]
] = [
    (
        CommandVerification(
            command=ShellCommand(command="ls ~", env={"TOKEN": "DUMMY"}),
        ),
        ("ls ~",),
        {
            "shell": True,
            "text": True,
            "check": False,
            "cwd": None,
            "capture_output": False,
            "encoding": sys.stdout.encoding,
        },
        {"TOKEN": "DUMMY"},
    ),
    (
        CommandVerification(
            command=ShellCommand(command=["ls", "~"], env={"TOKEN": "DUMMY"}),
        ),
        (["ls", "~"],),
        {
            "shell": False,
            "text": True,
            "check": False,
            "cwd": None,
            "capture_output": False,
            "encoding": sys.stdout.encoding,
        },
        {"TOKEN": "DUMMY"},
    ),
]


@pytest.mark.parametrize(
    "obj, args, kwargs, env",
    test_run_with_env_params,
    ids=range(len(test_run_with_env_params)),
)
def test_run_with_env(
    obj: Verification,
    args: Sequence[Any],
    kwargs: dict[str, Any],
    env: dict[str, str],
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
    mock_exec_command.assert_called_once()
    assert mock_exec_command.call_args[0] == args

    call_kwargs: dict[str, Any] = mock_exec_command.call_args[1]
    assert dict(call_kwargs["env"].items() & env.items()) == env
    assert len(call_kwargs["env"]) > len(env)
    del call_kwargs["env"]
    assert call_kwargs == kwargs


test_run_problem_command_params: list[tuple[ProblemVerification, OjTestArguments]] = [
    (
        ProblemVerification(command="ls ~", problem="https://example.com"),
        OjTestArguments(
            cookie=pathlib.Path("/any/cache/cookie.txt"),
            directory=pathlib.Path("/any/test"),
            judge=None,
            command="ls ~",
            tle=22.0,
            error=None,
            mle=128,
            env=None,
        ),
    ),
    (
        ProblemVerification(
            compile="cat LICENSE", command="ls ~", problem="https://example.com"
        ),
        OjTestArguments(
            cookie=pathlib.Path("/any/cache/cookie.txt"),
            directory=pathlib.Path("/any/test"),
            judge=None,
            command="ls ~",
            tle=22.0,
            error=None,
            mle=128,
            env=None,
        ),
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
        OjTestArguments(
            cookie=pathlib.Path("/any/cache/cookie.txt"),
            directory=pathlib.Path("/any/test"),
            judge=None,
            command="ls ~",
            tle=2.0,
            error=1e-06,
            mle=1.2,
            env=None,
        ),
    ),
    (
        ProblemVerification(
            compile=ShellCommand(command="cat LICENSE", env={"ARG": "VAR"}),
            command="ls ~",
            problem="https://judge.yosupo.jp/problem/aplusb",
            error=1e-6,
            tle=2,
        ),
        OjTestArguments(
            cookie=pathlib.Path("/any/cache/cookie.txt"),
            directory=pathlib.Path("/any/test"),
            judge=None,
            command="ls ~",
            tle=2.0,
            error=1e-06,
            mle=128,
            env=None,
        ),
    ),
    (
        ProblemVerification(
            compile="cat LICENSE",
            command=ShellCommand(command="ls ~", env={"ARG": "VAR"}),
            problem="https://judge.yosupo.jp/problem/aplusb",
            error=1e-6,
            tle=2,
        ),
        OjTestArguments(
            cookie=pathlib.Path("/any/cache/cookie.txt"),
            directory=pathlib.Path("/any/test"),
            judge=None,
            command="ls ~",
            tle=2.0,
            error=1e-06,
            mle=128,
            env={"ARG": "VAR"},
        ),
    ),
]


@pytest.mark.parametrize(
    "obj, args",
    test_run_problem_command_params,
    ids=range(len(test_run_problem_command_params)),
)
def test_run_problem_command(
    obj: ProblemVerification,
    args: OjTestArguments,
    mocker: MockerFixture,
):
    patch = mocker.patch.object(competitive_verifier.oj.tools.test_command, "run")

    mocker.patch(
        "competitive_verifier.oj.tools.test_command.get_cache_directory",
        return_value=pathlib.Path("/any/cache"),
    )
    mocker.patch(
        "competitive_verifier.oj.tools.test_command.get_directory",
        return_value=pathlib.Path("/any/"),
    )

    obj.run(
        DataVerificationParams(default_tle=22, default_mle=128),
    )
    patch.assert_called_once_with(args)


test_run_compile_params: list[
    tuple[Verification, Optional[Union[str, list[str]]], Optional[dict[str, Any]]]
] = [
    (
        CommandVerification(command="ls ~"),
        None,
        None,
    ),
    (
        CommandVerification(compile="cat LICENSE", command="ls ~"),
        "cat LICENSE",
        {
            "shell": True,
            "text": True,
            "check": False,
            "env": None,
            "cwd": None,
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
        "cat LICENSE",
        {
            "shell": True,
            "text": True,
            "check": False,
            "env": None,
            "cwd": None,
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
        "cat LICENSE",
        {
            "shell": True,
            "text": True,
            "check": False,
            "env": None,
            "cwd": None,
            "capture_output": False,
            "encoding": sys.stdout.encoding,
        },
    ),
    (
        ProblemVerification(
            compile=["cat", "LICENSE"],
            command="ls ~",
            problem="https://example.com",
            error=1e-6,
            tle=2,
        ),
        ["cat", "LICENSE"],
        {
            "shell": False,
            "text": True,
            "check": False,
            "env": None,
            "cwd": None,
            "capture_output": False,
            "encoding": sys.stdout.encoding,
        },
    ),
    (
        ProblemVerification(
            compile=ShellCommand(
                command=["cat", "LICENSE"],
                cwd=pathlib.Path("~/foo"),
            ),
            command="ls ~",
            problem="https://example.com",
            error=1e-6,
            tle=2,
        ),
        ["cat", "LICENSE"],
        {
            "shell": False,
            "text": True,
            "check": False,
            "env": None,
            "cwd": pathlib.Path("~/foo"),
            "capture_output": False,
            "encoding": sys.stdout.encoding,
        },
    ),
]


@pytest.mark.parametrize(
    "obj, args, kwargs",
    test_run_compile_params,
    ids=range(len(test_run_compile_params)),
)
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
        mock_exec_command.assert_called_once_with(args, **kwargs)


test_params_run_params: list[tuple[Verification, Optional[str]]] = [
    (ConstVerification(status=ResultStatus.SUCCESS), None),
    (CommandVerification(command="true"), None),
    (
        ProblemVerification(command="true", problem="http://example.com"),
        "ProblemVerification.run requires VerificationParams",
    ),
]


@pytest.mark.parametrize(
    "obj, error_message",
    test_params_run_params,
    ids=range(len(test_params_run_params)),
)
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
