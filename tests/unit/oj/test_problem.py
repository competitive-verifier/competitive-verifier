import pathlib

import pytest
from pytest_mock import MockerFixture

from competitive_verifier.models import TestCaseData as SystemTestCaseData
from competitive_verifier.oj.problem import (
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
def test_oj_problem_testdata_hash(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    mocker: MockerFixture,
):
    monkeypatch.setenv("COMPETITIVE_VERIFY_CONFIG_PATH", str(tmp_path))
    problem = YukicoderProblem(problem_no=1088)
    assert problem.testdata_hash() is None

    cases = [
        SystemTestCaseData("a", b"1 2\n", b"3\n"),
        SystemTestCaseData("b", b"5 6\n", b"11\n"),
    ]
    download = mocker.patch.object(
        YukicoderProblem, "_download_cases", return_value=cases
    )
    assert problem.download_system_cases()
    download.assert_called_once()
    downloaded = problem.testdata_hash()
    assert downloaded is not None
    assert problem.testdata_hash() == downloaded
    assert LocalProblem(problem.test_directory).testdata_hash() == downloaded

    # Cached cases are reused, so the hash describes the cases actually tested.
    (problem.test_directory / "b.out").write_bytes(b"12\n")
    assert problem.download_system_cases()
    download.assert_called_once()
    changed = problem.testdata_hash()
    assert changed != downloaded
    assert LocalProblem(problem.test_directory).testdata_hash() == changed
