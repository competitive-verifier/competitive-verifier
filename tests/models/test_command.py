# flake8: noqa E501
from typing import Optional

import pytest
from pydantic import BaseModel

from competitive_verifier.models.command import (
    Command,
    DummyCommand,
    ProblemVerificationCommand,
    VerificationCommand,
)

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


@pytest.mark.parametrize("obj, command, compile", command_command_params)
def test_command_command(
    obj: Command,
    command: Optional[str],
    compile: Optional[str],
):
    assert obj.get_command == command
    assert obj.get_compile_command == compile
