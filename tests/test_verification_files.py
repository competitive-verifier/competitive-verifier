import pathlib

import pytest

from competitive_verifier.models.file import VerificationFile, VerificationFiles

_test_files = VerificationFiles(
    files=[
        VerificationFile(path=pathlib.Path("foo/bar1.py"), dependencies=[]),
        VerificationFile(
            path=pathlib.Path("foo/bar2.py"),
            dependencies=[pathlib.Path("foo/bar1.py")],
        ),
        VerificationFile(path=pathlib.Path("foo/baz.py"), dependencies=[]),
        VerificationFile(
            path=pathlib.Path("foo/barbaz.py"),
            dependencies=[
                pathlib.Path("foo/bar2.py"),
                pathlib.Path("foo/baz.py"),
            ],
        ),
        VerificationFile(
            path=pathlib.Path("hoge/1.py"),
            dependencies=[],
        ),
        VerificationFile(
            path=pathlib.Path("hoge/hoge.py"),
            dependencies=[
                pathlib.Path("hoge/fuga.py"),
                pathlib.Path("hoge/1.py"),
            ],
        ),
        VerificationFile(
            path=pathlib.Path("hoge/piyo.py"),
            dependencies=[
                pathlib.Path("hoge/fuga.py"),
                pathlib.Path("hoge/hoge.py"),
            ],
        ),
        VerificationFile(
            path=pathlib.Path("hoge/fuga.py"),
            dependencies=[
                pathlib.Path("hoge/piyo.py"),
            ],
        ),
        VerificationFile(
            path=pathlib.Path("hoge/piyopiyo.py"),
            dependencies=[
                pathlib.Path("hoge/piyo.py"),
            ],
        ),
    ]
)


def test_files_dict():
    expected = {
        pathlib.Path("foo/bar1.py"): VerificationFile(
            path=pathlib.Path("foo/bar1.py"), dependencies=[]
        ),
        pathlib.Path("foo/bar2.py"): VerificationFile(
            path=pathlib.Path("foo/bar2.py"),
            dependencies=[pathlib.Path("foo/bar1.py")],
        ),
        pathlib.Path("foo/baz.py"): VerificationFile(
            path=pathlib.Path("foo/baz.py"), dependencies=[]
        ),
        pathlib.Path("foo/barbaz.py"): VerificationFile(
            path=pathlib.Path("foo/barbaz.py"),
            dependencies=[
                pathlib.Path("foo/bar2.py"),
                pathlib.Path("foo/baz.py"),
            ],
        ),
        pathlib.Path("hoge/1.py"): VerificationFile(
            path=pathlib.Path("hoge/1.py"),
            dependencies=[],
        ),
        pathlib.Path("hoge/hoge.py"): VerificationFile(
            path=pathlib.Path("hoge/hoge.py"),
            dependencies=[
                pathlib.Path("hoge/fuga.py"),
                pathlib.Path("hoge/1.py"),
            ],
        ),
        pathlib.Path("hoge/piyo.py"): VerificationFile(
            path=pathlib.Path("hoge/piyo.py"),
            dependencies=[
                pathlib.Path("hoge/fuga.py"),
                pathlib.Path("hoge/hoge.py"),
            ],
        ),
        pathlib.Path("hoge/fuga.py"): VerificationFile(
            path=pathlib.Path("hoge/fuga.py"),
            dependencies=[
                pathlib.Path("hoge/piyo.py"),
            ],
        ),
        pathlib.Path("hoge/piyopiyo.py"): VerificationFile(
            path=pathlib.Path("hoge/piyopiyo.py"),
            dependencies=[
                pathlib.Path("hoge/piyo.py"),
            ],
        ),
    }

    assert len(_test_files.files_dict) == len(expected)
    for k, v in _test_files.files_dict.items():
        assert expected[k].__dict__ == v.__dict__

    # cache
    assert _test_files.files_dict is _test_files.files_dict


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
    expected_paths = set(pathlib.Path(p) for p in expected)
    assert expected_paths == _test_files.resolve_dependencies(pathlib.Path(path))
    assert expected_paths == _test_files.resolve_dependencies(pathlib.Path(path))
