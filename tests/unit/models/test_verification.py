import os
import pathlib
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, NamedTuple
from unittest.mock import PropertyMock

import pytest
from pydantic import TypeAdapter
from pytest_mock import MockerFixture

import competitive_verifier.oj.tools.oj_test
from competitive_verifier.models import (
    CommandVerification,
    ConstVerification,
    Problem,
    ProblemVerification,
    ResultStatus,
    ShellCommand,
    Verification,
)
from competitive_verifier.oj.tools.oj_test import OjTestArguments


@dataclass
class DataVerificationParams:
    default_tle: float | None
    default_mle: float | None


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


@pytest.mark.parametrize(
    ("obj", "raw_json", "output_json"),
    test_command_union_json_params,
    ids=lambda s: s[:20] if isinstance(s, str) else s,
)
def test_command_union_json(
    obj: Verification,
    raw_json: str,
    output_json: str,
):
    assert obj == type(obj).model_validate_json(raw_json)
    assert obj.model_dump_json(exclude_none=True) == output_json

    assert obj == TypeAdapter(Verification).validate_json(raw_json)


def test_const_verification(mocker: MockerFixture):
    mock_exec_command = mocker.patch("subprocess.run")
    obj = ConstVerification(status=ResultStatus.SUCCESS)

    assert obj.run() == ResultStatus.SUCCESS
    assert obj.run_compile_command()
    mock_exec_command.assert_not_called()


test_run_params: list[tuple[Verification, tuple[str | list[str]], dict[str, Any]]] = [
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
    ("obj", "args", "kwargs"),
    test_run_params,
)
def test_run(
    obj: Verification,
    args: Sequence[Any],
    kwargs: dict[str, Any],
    mocker: MockerFixture,
):
    mock_exec_command = mocker.patch("subprocess.run")
    obj.run(
        DataVerificationParams(
            default_tle=22,
            default_mle=128,
        ),
    )
    mock_exec_command.assert_called_once_with(*args, **kwargs)


test_run_with_env_params: list[
    tuple[Verification, tuple[str | list[str]], dict[str, Any], dict[str, str]]
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
    ("obj", "args", "kwargs", "env"),
    test_run_with_env_params,
)
def test_run_with_env(
    obj: Verification,
    args: Sequence[Any],
    kwargs: dict[str, Any],
    env: dict[str, str],
    mocker: MockerFixture,
):
    mock_exec_command = mocker.patch("subprocess.run")
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
        ProblemVerification(
            command="ls ~",
            problem="http://judge.u-aizu.ac.jp/onlinejudge/description.jsp?id=1169",
        ),
        OjTestArguments(
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
            problem="http://judge.u-aizu.ac.jp/onlinejudge/description.jsp?id=1169",
        ),
        OjTestArguments(
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
            problem="http://judge.u-aizu.ac.jp/onlinejudge/description.jsp?id=1169",
            error=1e-6,
            tle=2,
            mle=1.2,
        ),
        OjTestArguments(
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
            directory=pathlib.Path("/any/test"),
            judge=pathlib.Path("/any/mockcheck"),
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
            directory=pathlib.Path("/any/test"),
            judge=pathlib.Path("/any/mockcheck"),
            command="ls ~",
            tle=2.0,
            error=1e-06,
            mle=128,
            env={"ARG": "VAR"},
        ),
    ),
]


@pytest.mark.parametrize(
    ("obj", "args"),
    test_run_problem_command_params,
)
def test_run_problem_command(
    obj: ProblemVerification,
    args: OjTestArguments,
    mocker: MockerFixture,
):
    mocker.patch(
        "competitive_verifier.oj.tools.problem.LibraryCheckerProblem.checker_exe_name",
        "mockcheck",
    )
    patch = mocker.patch.object(competitive_verifier.oj.tools.oj_test, "_run")

    mocker.patch.object(
        Problem,
        "problem_directory",
        new_callable=PropertyMock,
        return_value=pathlib.Path("/any/"),
    )

    obj.run(
        DataVerificationParams(default_tle=22, default_mle=128),
    )
    patch.assert_called_once_with(args)


test_run_compile_params: list[
    tuple[Verification, str | list[str] | None, dict[str, Any] | None]
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
    ("obj", "args", "kwargs"),
    test_run_compile_params,
)
def test_run_compile(
    obj: Verification,
    args: Sequence[Any] | None,
    kwargs: dict[str, Any] | None,
    mocker: MockerFixture,
):
    mock_exec_command = mocker.patch("subprocess.run")
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


test_params_run_params: list[tuple[Verification, str | None]] = [
    (ConstVerification(status=ResultStatus.SUCCESS), None),
    (CommandVerification(command="true"), None),
    (
        ProblemVerification(command="true", problem="http://example.com"),
        "ProblemVerification.run requires VerificationParams",
    ),
]


@pytest.mark.parametrize(
    ("obj", "error_message"),
    test_params_run_params,
)
def test_params_run(
    obj: Verification,
    error_message: str | None,
    mocker: MockerFixture,
):
    mocker.patch("subprocess.run")
    if error_message:
        with pytest.raises(ValueError, match=error_message) as e:
            obj.run()
        assert e.value.args == (error_message,)
    else:
        obj.run()


@pytest.mark.parametrize(
    "status", [ResultStatus.FAILURE, ResultStatus.SKIPPED, ResultStatus.SUCCESS]
)
def test_run_const_verification(status: ResultStatus):
    obj = ConstVerification(name="name", status=status)
    assert obj.run_compile_command()
    assert obj.run() == status


class Return(NamedTuple):
    returncode: int


class TestCommandVerification:
    def test_command(self, mocker: MockerFixture):
        mockrun = mocker.patch("subprocess.run", return_value=Return(0))
        obj = CommandVerification(name="name", command="echo 1")

        assert obj.run_compile_command()
        assert obj.run() == ResultStatus.SUCCESS
        mockrun.assert_called_once_with(
            "echo 1",
            capture_output=False,
            check=False,
            cwd=None,
            encoding="utf-8",
            env=None,
            shell=True,
            text=True,
        )

    def test_command_failure(self, mocker: MockerFixture):
        mockrun = mocker.patch("subprocess.run", return_value=Return(1))
        obj = CommandVerification(name="name", command=["echo", "1"])

        assert obj.run_compile_command()
        assert obj.run() == ResultStatus.FAILURE
        mockrun.assert_called_once_with(
            ["echo", "1"],
            capture_output=False,
            check=False,
            cwd=None,
            encoding="utf-8",
            env=None,
            shell=False,
            text=True,
        )

    def test_command_and_compile(self, mocker: MockerFixture):
        mocker.patch.dict(os.environ, {"DEFAULT": "dd"}, clear=True)
        mockrun = mocker.patch("subprocess.run", return_value=Return(0))
        obj = CommandVerification(
            name="name",
            compile="echo 1",
            command=ShellCommand(
                command="ls .",
                env={"MOCK": "mocker"},
                cwd=pathlib.Path("/root"),
            ),
        )

        assert obj.run_compile_command()
        mockrun.assert_called_once_with(
            "echo 1",
            capture_output=False,
            check=False,
            cwd=None,
            encoding="utf-8",
            env=None,
            shell=True,
            text=True,
        )
        mockrun.reset_mock()

        assert obj.run() == ResultStatus.SUCCESS
        mockrun.assert_called_once_with(
            "ls .",
            capture_output=False,
            check=False,
            cwd=pathlib.Path("/root"),
            encoding="utf-8",
            env={"DEFAULT": "dd", "MOCK": "mocker"},
            shell=True,
            text=True,
        )

    def test_tempdir(self, mocker: MockerFixture):
        mocker.patch.dict(os.environ, {"DEFAULT": "dd"}, clear=True)
        mockrun = mocker.patch("subprocess.run", return_value=Return(0))

        mockmkdir = mocker.patch.object(pathlib.Path, "mkdir")

        obj = CommandVerification(
            name="name",
            compile="echo 1",
            command=ShellCommand(
                command="ls .",
                env={"MOCK": "mocker"},
                cwd=pathlib.Path("/root"),
            ),
            tempdir=pathlib.Path("/root/tmp"),
        )

        assert obj.run_compile_command()
        mockmkdir.assert_called_once_with(exist_ok=True, parents=True)
        mockrun.assert_called_once_with(
            "echo 1",
            capture_output=False,
            check=False,
            cwd=None,
            encoding="utf-8",
            env=None,
            shell=True,
            text=True,
        )
        mockmkdir.reset_mock()
        mockrun.reset_mock()

        assert obj.run() == ResultStatus.SUCCESS
        mockmkdir.assert_called_once_with(exist_ok=True, parents=True)
        mockrun.assert_called_once_with(
            "ls .",
            capture_output=False,
            check=False,
            cwd=pathlib.Path("/root"),
            encoding="utf-8",
            env={"DEFAULT": "dd", "MOCK": "mocker"},
            shell=True,
            text=True,
        )
