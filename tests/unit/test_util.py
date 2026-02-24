import pathlib
from typing import NamedTuple

import pytest

from competitive_verifier.util import resolve_relative_or_abs_path


class DirStructure(NamedTuple):
    name: str
    items: "list[str|DirStructure]"


@pytest.mark.allow_mkdir
def test_resolve_relative_or_abs_path(
    monkeypatch: pytest.MonkeyPatch,
    testtemp: pathlib.Path,
):
    def setup(cwd: pathlib.Path, d: DirStructure):
        dd = cwd / d.name
        dd.mkdir()
        for c in d.items:
            if isinstance(c, str):
                (dd / c).touch()
            else:
                setup(dd, c)

    setup(
        testtemp,
        DirStructure(
            "root",
            [
                "outer",
                DirStructure(
                    "dir1",
                    ["file1.txt", DirStructure("subdirA", ["a1.cb1.c"])],
                ),
                DirStructure(
                    "dir2",
                    ["file1.txt", DirStructure("subdirB", ["a1.cb1.c"])],
                ),
            ],
        ),
    )
    monkeypatch.chdir(testtemp / "root")

    assert (
        resolve_relative_or_abs_path(str(testtemp / "outer"), basedir=testtemp / "root")
        is None
    )

    assert resolve_relative_or_abs_path(
        "./file1.txt", basedir=testtemp / "root/dir1"
    ) == pathlib.Path("dir1/file1.txt")

    assert resolve_relative_or_abs_path(
        "../dir2/file1.txt", basedir=testtemp / "root/dir1"
    ) == pathlib.Path("dir2/file1.txt")

    assert (
        resolve_relative_or_abs_path("./file2.txt", basedir=testtemp / "root/dir1")
        is None
    )

    assert (
        resolve_relative_or_abs_path(
            "../dir2/file2.txt", basedir=testtemp / "root/dir1"
        )
        is None
    )

    assert resolve_relative_or_abs_path(
        "//dir1/file1.txt", basedir=testtemp / "root/dir1"
    ) == pathlib.Path("dir1/file1.txt")

    assert resolve_relative_or_abs_path(
        "//dir2/file1.txt", basedir=testtemp / "root/dir1"
    ) == pathlib.Path("dir2/file1.txt")

    assert (
        resolve_relative_or_abs_path("//file2.txt", basedir=testtemp / "root/dir1")
        is None
    )

    assert resolve_relative_or_abs_path(
        "file1.txt", basedir=testtemp / "root/dir1"
    ) == pathlib.Path("dir1/file1.txt")

    assert resolve_relative_or_abs_path(
        str(testtemp / "root/dir1/file1.txt"), basedir=testtemp / "root/dir1"
    ) == pathlib.Path("dir1/file1.txt")
