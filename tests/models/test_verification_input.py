# flake8: noqa E501
import json
from pathlib import Path
from typing import Any

import pytest

from competitive_verifier.models import VerificationFile, VerificationInput

test_input = VerificationInput(
    files={
        Path("foo/bar1.py"): VerificationFile(dependencies=[]),
        Path("foo/bar2.py"): VerificationFile(
            dependencies=[Path("foo/bar1.py")],
        ),
        Path("foo/baz.py"): VerificationFile(dependencies=[]),
        Path("foo/barbaz.py"): VerificationFile(
            dependencies=[
                Path("foo/bar2.py"),
                Path("foo/baz.py"),
            ],
        ),
        Path("hoge/1.py"): VerificationFile(
            dependencies=[],
        ),
        Path("hoge/hoge.py"): VerificationFile(
            dependencies=[
                Path("hoge/fuga.py"),
                Path("hoge/1.py"),
            ],
        ),
        Path("hoge/piyo.py"): VerificationFile(
            dependencies=[
                Path("hoge/fuga.py"),
                Path("hoge/hoge.py"),
            ],
        ),
        Path("hoge/fuga.py"): VerificationFile(
            dependencies=[
                Path("hoge/piyo.py"),
            ],
        ),
        Path("hoge/piyopiyo.py"): VerificationFile(
            dependencies=[
                Path("hoge/piyo.py"),
            ],
        ),
    }
)


resolve_dependencies_params: list[tuple[str, list[str]]] = [
    ("foo/bar1.py", ["foo/bar1.py"]),
    ("foo/bar2.py", ["foo/bar1.py", "foo/bar2.py"]),
    ("foo/baz.py", ["foo/baz.py"]),
    ("foo/barbaz.py", ["foo/barbaz.py", "foo/baz.py", "foo/bar1.py", "foo/bar2.py"]),
    ("hoge/1.py", ["hoge/1.py"]),
    (
        "hoge/hoge.py",
        ["hoge/hoge.py", "hoge/piyo.py", "hoge/fuga.py", "hoge/1.py"],
    ),
    (
        "hoge/piyo.py",
        ["hoge/hoge.py", "hoge/piyo.py", "hoge/fuga.py", "hoge/1.py"],
    ),
    (
        "hoge/fuga.py",
        ["hoge/hoge.py", "hoge/piyo.py", "hoge/fuga.py", "hoge/1.py"],
    ),
    (
        "hoge/piyopiyo.py",
        [
            "hoge/piyopiyo.py",
            "hoge/hoge.py",
            "hoge/piyo.py",
            "hoge/fuga.py",
            "hoge/1.py",
        ],
    ),
]


@pytest.mark.parametrize(
    "path, expected",
    resolve_dependencies_params,
    ids=[tup[0] for tup in resolve_dependencies_params],
)
def test_resolve_dependencies(path: str, expected: list[str]):
    expected_paths = set(Path(p) for p in expected)
    assert expected_paths == test_input.resolve_dependencies(Path(path))
    assert expected_paths == test_input.resolve_dependencies(Path(path))


def test_to_dict():
    assert test_input.dict() == test_input.impl.dict()


def test_to_json():
    assert test_input.json() == test_input.impl.json()

    obj = VerificationInput.parse_obj(
        {
            "pre_command": "ls .",
            "files": {
                "foo/bar.py": {},
                "foo/baz.py": {
                    "path": "foo/baz.py",
                    "display_path": "baz.py",
                    "dependencies": ["foo/bar.py"],
                    "verification": [{"type": "dummy"}],
                },
            },
        }
    )
    assert json.loads(obj.json()) == {
        "pre_command": ["ls ."],
        "files": {
            str(Path("foo/bar.py")): {
                "dependencies": [],
                "display_path": None,
                "verification": [],
            },
            str(Path("foo/baz.py")): {
                "display_path": str(Path("baz.py")),
                "dependencies": [str(Path("foo/bar.py"))],
                "verification": [{"type": "dummy"}],
            },
        },
    }


def test_repr():
    obj = VerificationInput.parse_obj(
        {
            "pre_command": "ls .",
            "files": {
                "foo/bar.py": {},
                "foo/baz.py": {
                    "path": "foo/baz.py",
                    "display_path": "baz.py",
                    "dependencies": ["foo/bar.py"],
                    "verification": [{"type": "dummy"}],
                },
            },
        }
    )
    assert repr(obj) == (
        "VerificationInput(pre_command=['ls .'], "
        + f"files={{{repr(Path('foo/bar.py'))}: VerificationFile(display_path=None, dependencies=[], verification=[]),"
        + f" {repr(Path('foo/baz.py'))}: VerificationFile(display_path={repr(Path('baz.py'))}, dependencies=[{repr(Path('foo/bar.py'))}], verification=[DummyCommand(type='dummy')])"
        + f"}})"
    )


parse_pre_command_params: list[Any] = [
    (
        VerificationInput(pre_command="ls .", files={}),
        {"pre_command": "ls ."},
    ),
    (
        VerificationInput(pre_command=["ls .", "true"], files={}),
        {"pre_command": ["ls .", "true"]},
    ),
    (
        VerificationInput(pre_command=None, files={}),
        {"pre_command": None},
    ),
]


@pytest.mark.parametrize("obj, raw_obj", parse_pre_command_params)
def test_parse_pre_command(obj: VerificationInput, raw_obj: dict[str, Any]):
    assert VerificationInput.parse_obj(raw_obj) == obj


pre_command_params: list[Any] = [
    (
        VerificationInput(pre_command="ls .", files={}),
        ["ls ."],
    ),
    (
        VerificationInput(pre_command=["ls .", "true"], files={}),
        ["ls .", "true"],
    ),
    (
        VerificationInput(pre_command=None, files={}),
        None,
    ),
]


@pytest.mark.parametrize("obj, pre_command", pre_command_params)
def test_pre_command(obj: VerificationInput, pre_command: Any):
    assert obj.pre_command == pre_command
