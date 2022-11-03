# flake8: noqa E501
from pathlib import Path
from typing import Any
from pydantic import ValidationError

import pytest

from competitive_verifier.models.file import VerificationFile, VerificationInput

test_input = VerificationInput(
    files=[
        VerificationFile(path=Path("foo/bar1.py"), dependencies=[]),
        VerificationFile(
            path=Path("foo/bar2.py"),
            dependencies=[Path("foo/bar1.py")],
        ),
        VerificationFile(path=Path("foo/baz.py"), dependencies=[]),
        VerificationFile(
            path=Path("foo/barbaz.py"),
            dependencies=[
                Path("foo/bar2.py"),
                Path("foo/baz.py"),
            ],
        ),
        VerificationFile(
            path=Path("hoge/1.py"),
            dependencies=[],
        ),
        VerificationFile(
            path=Path("hoge/hoge.py"),
            dependencies=[
                Path("hoge/fuga.py"),
                Path("hoge/1.py"),
            ],
        ),
        VerificationFile(
            path=Path("hoge/piyo.py"),
            dependencies=[
                Path("hoge/fuga.py"),
                Path("hoge/hoge.py"),
            ],
        ),
        VerificationFile(
            path=Path("hoge/fuga.py"),
            dependencies=[
                Path("hoge/piyo.py"),
            ],
        ),
        VerificationFile(
            path=Path("hoge/piyopiyo.py"),
            dependencies=[
                Path("hoge/piyo.py"),
            ],
        ),
    ]
)


def test_files_dict():
    expected = {
        Path("foo/bar1.py"): VerificationFile(
            path=Path("foo/bar1.py"), dependencies=[]
        ),
        Path("foo/bar2.py"): VerificationFile(
            path=Path("foo/bar2.py"),
            dependencies=[Path("foo/bar1.py")],
        ),
        Path("foo/baz.py"): VerificationFile(path=Path("foo/baz.py"), dependencies=[]),
        Path("foo/barbaz.py"): VerificationFile(
            path=Path("foo/barbaz.py"),
            dependencies=[
                Path("foo/bar2.py"),
                Path("foo/baz.py"),
            ],
        ),
        Path("hoge/1.py"): VerificationFile(
            path=Path("hoge/1.py"),
            dependencies=[],
        ),
        Path("hoge/hoge.py"): VerificationFile(
            path=Path("hoge/hoge.py"),
            dependencies=[
                Path("hoge/fuga.py"),
                Path("hoge/1.py"),
            ],
        ),
        Path("hoge/piyo.py"): VerificationFile(
            path=Path("hoge/piyo.py"),
            dependencies=[
                Path("hoge/fuga.py"),
                Path("hoge/hoge.py"),
            ],
        ),
        Path("hoge/fuga.py"): VerificationFile(
            path=Path("hoge/fuga.py"),
            dependencies=[
                Path("hoge/piyo.py"),
            ],
        ),
        Path("hoge/piyopiyo.py"): VerificationFile(
            path=Path("hoge/piyopiyo.py"),
            dependencies=[
                Path("hoge/piyo.py"),
            ],
        ),
    }

    assert len(test_input.files_dict) == len(expected)
    for k, v in test_input.files_dict.items():
        assert vars(expected[k]) == vars(v)

    # cache
    assert test_input.files_dict is test_input.files_dict


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


def test_repr():
    obj = VerificationInput.parse_obj(
        {
            "pre_command": "ls .",
            "files": [
                {"path": "foo/bar.py"},
                {
                    "path": "foo/baz.py",
                    "display_path": "baz.py",
                    "dependencies": ["foo/bar.py"],
                    "verification": [{"type": "dummy"}],
                },
            ],
        }
    )
    assert repr(obj) == (
        "VerificationInput(pre_command=['ls .'], "
        + f"files=[VerificationFile(path={repr(Path('foo/bar.py'))}, display_path=None, dependencies=[], verification=[]),"
        + f" VerificationFile(path={repr(Path('foo/baz.py'))}, display_path={repr(Path('baz.py'))}, dependencies=[{repr(Path('foo/bar.py'))}], verification=[DummyCommand(type='dummy')])"
        + f"])"
    )


parse_pre_command_params: list[Any] = [
    (
        VerificationInput(pre_command="ls .", files=[]),
        {"pre_command": "ls ."},
    ),
    (
        VerificationInput(pre_command=["ls .", "true"], files=[]),
        {"pre_command": ["ls .", "true"]},
    ),
    (
        VerificationInput(pre_command=None, files=[]),
        {"pre_command": None},
    ),
]


@pytest.mark.parametrize("obj, raw_obj", parse_pre_command_params)
def test_parse_pre_command(obj: VerificationInput, raw_obj: dict[str, Any]):
    assert VerificationInput.parse_obj(raw_obj) == obj


pre_command_params: list[Any] = [
    (
        VerificationInput(pre_command="ls .", files=[]),
        ["ls ."],
    ),
    (
        VerificationInput(pre_command=["ls .", "true"], files=[]),
        ["ls .", "true"],
    ),
    (
        VerificationInput(pre_command=None, files=[]),
        None,
    ),
]


@pytest.mark.parametrize("obj, pre_command", pre_command_params)
def test_pre_command(obj: VerificationInput, pre_command: Any):
    assert obj.pre_command == pre_command


duplicate_path_error_params = [  # type: ignore
    (
        {
            "files": [
                {"path": "foo/bar.sh"},
                {"path": "foo/bar.sh"},
                {"path": "foo/baz.sh"},
                {"path": "hoge/piyo.sh"},
            ],
        },
        f"Duplicate files.path {str(Path('foo/bar.sh'))}",
    ),
    (
        {
            "files": [
                {"path": "foo/bar.sh"},
                {"path": "foo/bar.sh"},
                {"path": "foo/bar.sh"},
                {"path": "foo/baz.sh"},
                {"path": "foo/bak.sh"},
                {"path": "foo/bar.sh"},
                {"path": "foo/baz.sh"},
                {"path": "hoge/piyo.sh"},
            ],
        },
        f"Duplicate files.path {str(Path('foo/bar.sh'))}, {str(Path('foo/baz.sh'))}",
    ),
]


@pytest.mark.parametrize("d, error_msg", duplicate_path_error_params)
def test_duplicate_path_error(d: dict[str, Any], error_msg: str):
    with pytest.raises(ValidationError) as e:
        VerificationInput.parse_obj(d)
    errors = e.value.errors()
    assert len(errors) == 1
    assert str(errors[0]["msg"]) == error_msg
