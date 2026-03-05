import pathlib
from typing import NamedTuple

import pytest
from pytest_mock import MockerFixture

from competitive_verifier.util import (
    normalize_bytes_text,
    read_text_normalized,
    resolve_referenced_path,
)


class DirStructure(NamedTuple):
    name: str
    items: "list[str|DirStructure]"


@pytest.mark.allow_mkdir
def test_resolve_referenced_path(
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
    (testtemp / "outer").touch()
    monkeypatch.chdir(testtemp / "root")

    assert (
        resolve_referenced_path(str(testtemp / "outer"), basedir=testtemp / "root")
        is None
    )

    assert resolve_referenced_path(
        "./file1.txt", basedir=testtemp / "root/dir1"
    ) == pathlib.Path("dir1/file1.txt")

    assert resolve_referenced_path(
        "../dir2/file1.txt", basedir=testtemp / "root/dir1"
    ) == pathlib.Path("dir2/file1.txt")

    assert (
        resolve_referenced_path("./file2.txt", basedir=testtemp / "root/dir1") is None
    )

    assert (
        resolve_referenced_path("../dir2/file2.txt", basedir=testtemp / "root/dir1")
        is None
    )

    assert resolve_referenced_path(
        "//dir1/file1.txt", basedir=testtemp / "root/dir1"
    ) == pathlib.Path("dir1/file1.txt")

    assert resolve_referenced_path(
        "//dir2/file1.txt", basedir=testtemp / "root/dir1"
    ) == pathlib.Path("dir2/file1.txt")

    assert (
        resolve_referenced_path("//file2.txt", basedir=testtemp / "root/dir1") is None
    )

    assert resolve_referenced_path(
        "file1.txt", basedir=testtemp / "root/dir1"
    ) == pathlib.Path("dir1/file1.txt")

    assert resolve_referenced_path(
        str(testtemp / "root/dir1/file1.txt"), basedir=testtemp / "root/dir1"
    ) == pathlib.Path("dir1/file1.txt")


def test_normalize_bytes_text(mocker: MockerFixture):
    cp932_text = (
        b"\x89J\x83j\x83\x82\x83}\x83P\x83Y\n"
        b"\x95\x97\x83j\x83\x82\x83}\x83P\x83Y\n"
        b"\x90\xe1\x83j\x83\x82\x89\xc4\x83m\x8f\x8b\x83T\x83j\x83\x82\x83}\x83P\x83k\n"
        b"\x8f\xe4\x95v\x83i\x83J\x83\x89\x83_\x83\x92\x83\x82\x83`\n"
        b"\x97|\x83n\x83i\x83N\n\x8c\x88\x83V\x83e\xe1\xd1\x83\x89\x83Y\n"
        b"\x83C\x83c\x83\x82\x83V\x83d\x83J\x83j\x83\x8f\x83\x89\x83b\x83e\x83\x90\x83\x8b\n"
        b"\x88\xea\x93\xfa\x83j\x8c\xba\x95\xc4\x8el\x8d\x87\x83g\n"
        b"\x96\xa1\x91X\x83g\x8f\xad\x83V\x83m\x96\xec\x8d\xd8\x83\x92\x83^\x83x\n"
        b"\x83A\x83\x89\x83\x86\x83\x8b\x83R\x83g\x83\x92\n"
        b"\x83W\x83u\x83\x93\x83\x92\x83J\x83\x93\x83W\x83\x87\x83E\x83j\x93\xfc\x83\x8c\x83Y\x83j\n"
        b"\x83\x88\x83N\x83~\x83L\x83L\x83V\x83\x8f\x83J\x83\x8a\n"
        b"\x83\\\x83V\x83e\x83\x8f\x83X\x83\x8c\x83Y\n"
        b"\x96\xec\x8c\xb4\xc9\x8f\xbc\xc9\x97\xd1\xc9\x89A\xc9\n"
        b"\x8f\xac\xbb\xc5\x8a\x9e\xcc\xde\xb7\xc9\x8f\xac\x89\xae\xc6\x83\x90\xc3\n"
        b"\x93\x8c\xc6\x95a\x8bC\xc9\xba\xc4\xde\xd3\xb1\xda\xca\xde\n"
        b"\x8ds\xaf\xc3\x8a\xc5\x95a\xbc\xc3\xd4\xd8\n"
        b"\x90\xbc\xc6\xc2\xb6\xda\xc0\x95\xea\xb1\xda\xca\xde\n"
        b"\x8ds\xaf\xc3\xbf\xc9\x88\xee\xc9\x91\xa9\xa6\x95\x89\xcb\n"
        b"\x93\xec\xc6\x8e\x80\xc6\xbb\xb3\xc5\x90l\xb1\xda\xca\xde\n"
        b"\x8ds\xaf\xc3\xba\xca\xb6\xde\xd7\xc5\xb8\xc3\xd3\xb2\x81R\xc4\xb2\xcb\n"
        b"\x96k\xc6\xb9\xdd\xb8\x83\x8e\xd4\xbf\xbc\xae\xb3\xb6\xde\xb1\xda\xca\xde\n"
        b"\xc2\xcf\xd7\xc5\xb2\xb6\xd7\xd4\xd2\xdb\xc4\xb2\xcb\n"
        b"\xcb\xc3\xde\xd8\xc9\xc4\xb7\xca\xc5\xd0\xc0\xde\xa6\xc5\xb6\xde\xbc\n"
        b"\xbb\xd1\xbb\xc9\xc5\xc2\xca\xb5\xdb\xb5\xdb\xb1\xd9\xb7\n"
        b"\xd0\xdd\xc5\xc6\xc3\xde\xb8\xc9\xce\xde\x81[\xc4\xd6\xca\xde\xda\n"
        b"\xce\xd2\xd7\xda\xd3\xbe\xbd\xde\n"
        b"\xb8\xc6\xd3\xbb\xda\xbd\xde\n"
        b"\xbb\xb3\xb2\xcc\xd3\xc9\xc6\n"
        b"\xdc\xc0\xbc\xca\xc5\xd8\xc0\xb2"
    )
    text = (
        "雨ニモマケズ\n風ニモマケズ\n雪ニモ夏ノ暑サニモマケヌ\n丈夫ナカラダヲモチ\n慾ハナク\n決シテ瞋ラズ\nイツモシヅカニワラッテヰル\n"
        "一日ニ玄米四合ト\n味噌ト少シノ野菜ヲタベ\nアラユルコトヲ\nジブンヲカンジョウニ入レズニ\nヨクミキキシワカリ\nソシテワスレズ\n野原ﾉ松ﾉ林ﾉ陰ﾉ\n"
        "小ｻﾅ萱ﾌﾞｷﾉ小屋ﾆヰﾃ\n東ﾆ病気ﾉｺﾄﾞﾓｱﾚﾊﾞ\n行ｯﾃ看病ｼﾃﾔﾘ\n西ﾆﾂｶﾚﾀ母ｱﾚﾊﾞ\n行ｯﾃｿﾉ稲ﾉ束ｦ負ﾋ\n南ﾆ死ﾆｻｳﾅ人ｱﾚﾊﾞ\n行ｯﾃｺﾊｶﾞﾗﾅｸﾃﾓｲヽﾄｲﾋ\n"
        "北ﾆｹﾝｸヮﾔｿｼｮｳｶﾞｱﾚﾊﾞ\nﾂﾏﾗﾅｲｶﾗﾔﾒﾛﾄｲﾋ\nﾋﾃﾞﾘﾉﾄｷﾊﾅﾐﾀﾞｦﾅｶﾞｼ\nｻﾑｻﾉﾅﾂﾊｵﾛｵﾛｱﾙｷ\nﾐﾝﾅﾆﾃﾞｸﾉﾎﾞーﾄﾖﾊﾞﾚ\nﾎﾒﾗﾚﾓｾｽﾞ\nｸﾆﾓｻﾚｽﾞ\nｻｳｲﾌﾓﾉﾆ\nﾜﾀｼﾊﾅﾘﾀｲ"
    )
    mocker.patch("pathlib.Path.read_bytes", return_value=cp932_text)

    assert normalize_bytes_text(cp932_text) == text
    assert read_text_normalized(pathlib.Path()) == text
