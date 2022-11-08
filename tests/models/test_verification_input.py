# flake8: noqa E501
import json
from pathlib import Path

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


test_resolve_dependencies_params: list[tuple[str, list[str]]] = [
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
    test_resolve_dependencies_params,
    ids=[tup[0] for tup in test_resolve_dependencies_params],
)
def test_resolve_dependencies(path: str, expected: list[str]):
    expected_paths = set(Path(p) for p in expected)
    assert expected_paths == test_input.resolve_dependencies(Path(path))
    assert expected_paths == test_input.resolve_dependencies(Path(path))


def test_to_dict():
    assert test_input.dict() == test_input.impl.dict()


def test_to_json():
    assert test_input.json() == test_input.impl.json()
    assert VerificationInput.parse_raw(test_input.json()) == test_input

    obj = VerificationInput.parse_obj(
        {
            "files": {
                "foo/bar.py": {},
                "foo/baz.py": {
                    "path": "foo/baz.py",
                    "display_path": "var/foo/baz.py",
                    "dependencies": ["foo/bar.py"],
                    "verification": [
                        {
                            "type": "const",
                            "status": "success",
                        }
                    ],
                },
            },
        }
    )
    assert json.loads(obj.json()) == {
        "files": {
            "foo/bar.py": {
                "dependencies": [],
                "display_path": None,
                "verification": [],
            },
            "foo/baz.py": {
                "display_path": "var/foo/baz.py",
                "dependencies": ["foo/bar.py"],
                "verification": [
                    {
                        "type": "const",
                        "status": "success",
                    }
                ],
            },
        },
    }


def test_repr():
    obj = VerificationInput.parse_obj(
        {
            "files": {
                "foo/bar.py": {},
                "foo/baz.py": {
                    "path": "foo/baz.py",
                    "display_path": "baz.py",
                    "dependencies": ["foo/bar.py"],
                    "verification": [
                        {
                            "type": "const",
                            "status": "success",
                        }
                    ],
                },
            },
        }
    )
    print(repr(obj))
    assert repr(obj) == (
        "VerificationInput("
        + f"files={{{repr(Path('foo/bar.py'))}: VerificationFile(display_path=None, dependencies=[], verification=[]),"
        + f" {repr(Path('foo/baz.py'))}: VerificationFile(display_path={repr(Path('baz.py'))}, dependencies=[{repr(Path('foo/bar.py'))}], verification=[ConstVerification(type='const', status=<ResultStatus.SUCCESS: 'success'>)])"
        + f"}})"
    )
