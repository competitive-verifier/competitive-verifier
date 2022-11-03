# flake8: noqa E501
from pathlib import Path

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


def test_repr():
    path_type_name = type(Path("")).__name__
    assert repr(test_input) == (
        "VerificationInputImpl("
        + "pre_command=None, "
        + "files=["
        + ("VerificationFile(path=" + f"{path_type_name}")
        + "('foo/bar1.py'), display_path=None, dependencies=[], verification=[]), "
        + ("VerificationFile(path=" + f"{path_type_name}")
        + ("('foo/bar2.py'), display_path=None, dependencies=[" + f"{path_type_name}")
        + "('foo/bar1.py')], verification=[]), "
        + ("VerificationFile(path=" + f"{path_type_name}")
        + "('foo/baz.py'), display_path=None, dependencies=[], verification=[]), "
        + ("VerificationFile(path=" + f"{path_type_name}")
        + ("('foo/barbaz.py'), display_path=None, dependencies=[" + f"{path_type_name}")
        + ("('foo/bar2.py'), " + f"{path_type_name}")
        + (
            "('foo/baz.py')], verification=[]), VerificationFile(path="
            + f"{path_type_name}"
        )
        + (
            "('hoge/1.py'), display_path=None, dependencies=[], verification=[]), VerificationFile(path="
            + f"{path_type_name}"
        )
        + ("('hoge/hoge.py'), display_path=None, dependencies=[" + f"{path_type_name}")
        + ("('hoge/fuga.py'), " + f"{path_type_name}")
        + (
            "('hoge/1.py')], verification=[]), VerificationFile(path="
            + f"{path_type_name}"
        )
        + ("('hoge/piyo.py'), display_path=None, dependencies=[" + f"{path_type_name}")
        + ("('hoge/fuga.py'), " + f"{path_type_name}")
        + (
            "('hoge/hoge.py')], verification=[]), VerificationFile(path="
            + f"{path_type_name}"
        )
        + ("('hoge/fuga.py'), display_path=None, dependencies=[" + f"{path_type_name}")
        + (
            "('hoge/piyo.py')], verification=[]), VerificationFile(path="
            + f"{path_type_name}"
        )
        + (
            "('hoge/piyopiyo.py'), display_path=None, dependencies=["
            + f"{path_type_name}"
        )
        + "('hoge/piyo.py')], verification=[])])"
    )


def test_dict():
    assert test_input.dict() == test_input.impl.dict()


def test_json():
    assert test_input.json() == test_input.impl.json()
