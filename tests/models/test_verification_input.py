# flake8: noqa E501
import json
from pathlib import Path

from competitive_verifier.models import (
    ConstVerification,
    VerificationFile,
    VerificationInput,
)

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
        Path("test/test.py"): VerificationFile(
            verification=[ConstVerification(status="success")],  # type:ignore
            dependencies=[
                Path("hoge/piyopiyo.py"),
            ],
        ),
    }
)


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


def test_transitive_depends_on():
    simple = {
        "foo/bar1.py": ["foo/bar1.py"],
        "foo/bar2.py": ["foo/bar1.py", "foo/bar2.py"],
        "foo/baz.py": ["foo/baz.py"],
        "foo/barbaz.py": ["foo/barbaz.py", "foo/baz.py", "foo/bar1.py", "foo/bar2.py"],
        "hoge/1.py": ["hoge/1.py"],
        "hoge/hoge.py": ["hoge/hoge.py", "hoge/piyo.py", "hoge/fuga.py", "hoge/1.py"],
        "hoge/piyo.py": ["hoge/hoge.py", "hoge/piyo.py", "hoge/fuga.py", "hoge/1.py"],
        "hoge/fuga.py": ["hoge/hoge.py", "hoge/piyo.py", "hoge/fuga.py", "hoge/1.py"],
        "hoge/piyopiyo.py": [
            "hoge/piyopiyo.py",
            "hoge/hoge.py",
            "hoge/piyo.py",
            "hoge/fuga.py",
            "hoge/1.py",
        ],
        "test/test.py": [
            "hoge/1.py",
            "hoge/fuga.py",
            "hoge/hoge.py",
            "hoge/piyo.py",
            "hoge/piyopiyo.py",
            "test/test.py",
        ],
    }
    expected = {Path(p): set(Path(s) for s in d) for p, d in simple.items()}

    assert test_input.transitive_depends_on == expected
    assert test_input.transitive_depends_on is test_input.transitive_depends_on
    assert test_input.transitive_depends_on == expected


def test_depends_on():
    simple = {
        "foo/bar1.py": [],
        "foo/bar2.py": [("foo/bar1.py")],
        "foo/baz.py": [],
        "foo/barbaz.py": ["foo/bar2.py", "foo/baz.py"],
        "hoge/1.py": [],
        "hoge/hoge.py": ["hoge/fuga.py", "hoge/1.py"],
        "hoge/piyo.py": ["hoge/fuga.py", "hoge/hoge.py"],
        "hoge/fuga.py": ["hoge/piyo.py"],
        "hoge/piyopiyo.py": ["hoge/piyo.py"],
        "test/test.py": ["hoge/piyopiyo.py"],
    }
    expected = {Path(p): set(Path(s) for s in d) for p, d in simple.items()}

    assert test_input.depends_on == expected
    assert test_input.depends_on is test_input.depends_on
    assert test_input.depends_on == expected


def test_required_by():
    simple = {
        "foo/bar1.py": ["foo/bar2.py"],
        "foo/bar2.py": ["foo/barbaz.py"],
        "foo/baz.py": ["foo/barbaz.py"],
        "foo/barbaz.py": [],
        "hoge/1.py": ["hoge/hoge.py"],
        "hoge/hoge.py": ["hoge/piyo.py"],
        "hoge/piyo.py": ["hoge/fuga.py", "hoge/piyopiyo.py"],
        "hoge/fuga.py": ["hoge/piyo.py", "hoge/hoge.py"],
        "hoge/piyopiyo.py": [],
        "test/test.py": [],
    }
    expected = {Path(p): set(Path(s) for s in d) for p, d in simple.items()}

    assert test_input.required_by == expected
    assert test_input.required_by is test_input.required_by
    assert test_input.required_by == expected


def test_verified_with():
    simple = {
        "foo/bar1.py": [],
        "foo/bar2.py": [],
        "foo/baz.py": [],
        "foo/barbaz.py": [],
        "hoge/1.py": [],
        "hoge/hoge.py": [],
        "hoge/piyo.py": [],
        "hoge/fuga.py": [],
        "hoge/piyopiyo.py": ["test/test.py"],
        "test/test.py": [],
    }
    expected = {Path(p): set(Path(s) for s in d) for p, d in simple.items()}
    assert test_input.verified_with == expected
    assert test_input.verified_with is test_input.verified_with
    assert test_input.verified_with == expected
