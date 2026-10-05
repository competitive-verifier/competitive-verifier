import hashlib
import pathlib

import pytest
from pytest_mock import MockerFixture

from competitive_verifier.config import COMPETITIVE_VERIFY_CONFIG_PATH
from competitive_verifier.oj.problem import (
    LibraryCheckerProblem,
    LocalProblem,
    YukicoderProblem,
    _normpath,  # pyright: ignore[reportPrivateUsage]
    problem_from_url,
)

test_normpath_params: list[tuple[str, str]] = [
    ("hoge/foo/bar", "hoge/foo/bar"),
    ("/foo/bar", "/foo/bar"),
    ("//foo/bar", "/foo/bar"),
]


@pytest.mark.parametrize(
    ("path", "expected"),
    test_normpath_params,
    ids=[t[0] for t in test_normpath_params],
)
def test_normpath(path: str, expected: str):
    assert _normpath(path) == expected


test_problem_repr_params = [
    (
        "https://onlinejudge.u-aizu.ac.jp/courses/lesson/2/ITP1/1/ITP1_1_A",
        "AOJProblem.from_url('http://judge.u-aizu.ac.jp/onlinejudge/description.jsp?id=ITP1_1_A')",
    ),
    (
        "https://onlinejudge.u-aizu.ac.jp/problems/ITP1_1_A",
        "AOJProblem.from_url('http://judge.u-aizu.ac.jp/onlinejudge/description.jsp?id=ITP1_1_A')",
    ),
    (
        "https://judge.u-aizu.ac.jp/onlinejudge/description.jsp?id=ITP1_1_A&lang=jp",
        "AOJProblem.from_url('http://judge.u-aizu.ac.jp/onlinejudge/description.jsp?id=ITP1_1_A')",
    ),
    (
        "https://onlinejudge.u-aizu.ac.jp/services/room.html#RitsCamp19Day2/problems/A",
        "AOJArenaProblem.from_url('https://onlinejudge.u-aizu.ac.jp/services/room.html#RitsCamp19Day2/problems/A')",
    ),
    (
        "https://old.yosupo.jp/problem/aplusb",
        "LibraryCheckerProblem.from_url('https://judge.yosupo.jp/problem/aplusb')",
    ),
    (
        "https://judge.yosupo.jp/problem/aplusb",
        "LibraryCheckerProblem.from_url('https://judge.yosupo.jp/problem/aplusb')",
    ),
    (
        "http://old.yosupo.jp/problem/aplusb",
        "LibraryCheckerProblem.from_url('https://judge.yosupo.jp/problem/aplusb')",
    ),
    (
        "http://judge.yosupo.jp/problem/aplusb",
        "LibraryCheckerProblem.from_url('https://judge.yosupo.jp/problem/aplusb')",
    ),
    (
        "https://yukicoder.me/problems/4573",
        "YukicoderProblem.from_url('https://yukicoder.me/problems/4573')",
    ),
    (
        "https://yukicoder.me/problems/no/1088",
        "YukicoderProblem.from_url('https://yukicoder.me/problems/no/1088')",
    ),
    (
        "http://yukicoder.me/problems/4573",
        "YukicoderProblem.from_url('https://yukicoder.me/problems/4573')",
    ),
    (
        "http://yukicoder.me/problems/no/1088",
        "YukicoderProblem.from_url('https://yukicoder.me/problems/no/1088')",
    ),
    (
        "http://yukicoder.me/4573",
        "None",
    ),
]


@pytest.mark.parametrize(
    ("url", "expected"),
    test_problem_repr_params,
    ids=[t[0] for t in test_problem_repr_params],
)
def test_problem_repr(url: str, expected: str):
    assert repr(problem_from_url(url)) == expected


@pytest.mark.allow_mkdir
def test_base_problem_is_testdata_cached(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setenv(COMPETITIVE_VERIFY_CONFIG_PATH, tmp_path.as_posix())
    p = YukicoderProblem(problem_no=1088)
    assert p.is_testdata_cached() is False

    p.test_directory.mkdir(parents=True)
    assert p.is_testdata_cached() is False

    (p.test_directory / "sample_00.in").write_text("1 2\n")
    assert p.is_testdata_cached() is True


@pytest.mark.allow_mkdir
def test_library_checker_is_testdata_cached(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setenv(COMPETITIVE_VERIFY_CONFIG_PATH, tmp_path.as_posix())
    p = LibraryCheckerProblem(problem_id="aplusb")
    assert p.is_testdata_cached() is False

    source = p.repo_path / "sample" / "aplusb"
    source.mkdir(parents=True)
    (source / "info.toml").write_text("")
    assert p.is_testdata_cached() is False

    (source / "in").mkdir()
    (source / "out").mkdir()
    (source / "in" / "example_00.in").write_text("1 2\n")
    assert p.is_testdata_cached() is False

    (source / "out" / "example_00.out").write_text("3\n")
    assert p.is_testdata_cached() is True


@pytest.mark.allow_mkdir
def test_local_problem_is_testdata_cached(tmp_path: pathlib.Path):
    assert LocalProblem(tmp_path / "missing").is_testdata_cached() is True


@pytest.fixture
def library_checker_repo(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> pathlib.Path:
    monkeypatch.setenv("COMPETITIVE_VERIFY_CONFIG_PATH", str(tmp_path))
    repo_path = tmp_path / "cache" / "library-checker-problems"
    (repo_path / "sample" / "aplusb").mkdir(parents=True)
    (repo_path / "sample" / "aplusb" / "info.toml").write_text("")
    return repo_path


@pytest.mark.allow_mkdir
def test_library_checker_testdata_hash(
    library_checker_repo: pathlib.Path,
    mocker: MockerFixture,
):
    update = mocker.patch.object(LibraryCheckerProblem, "update_cloned_repository")
    problem = LibraryCheckerProblem(problem_id="aplusb")
    hash_json = library_checker_repo / "sample" / "aplusb" / "hash.json"
    assert problem.hash_json == hash_json

    assert problem.testdata_hash() is None

    hash_json.write_bytes(b'{"example_00.in": "0" * 64}')
    assert problem.testdata_hash() == hashlib.sha256(hash_json.read_bytes()).hexdigest()
    assert problem.testdata_hash() == problem.testdata_hash()

    hash_json.write_bytes(b'{"example_00.in": "1" * 64}')
    assert problem.testdata_hash() == hashlib.sha256(hash_json.read_bytes()).hexdigest()

    update.assert_not_called()


@pytest.mark.allow_mkdir
@pytest.mark.usefixtures("library_checker_repo")
def test_library_checker_testdata_hash_unknown_problem():
    problem = LibraryCheckerProblem(problem_id="no_such_problem")
    assert problem.testdata_hash() is None


def test_library_checker_sync_testdata(mocker: MockerFixture):
    update = mocker.patch.object(LibraryCheckerProblem, "update_cloned_repository")
    LibraryCheckerProblem(problem_id="aplusb").sync_testdata()
    update.assert_called_once_with()


def test_base_problem_sync_testdata():
    assert YukicoderProblem(problem_no=1088).sync_testdata() is None
