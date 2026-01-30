import gc

import pytest

from competitive_verifier.oj.tools.problem import Problem, normpath

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
    assert normpath(path) == expected


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
    assert repr(Problem.from_url(url)) == expected


def test_problem_from_url_invalid_class():
    class DummyProblem(Problem):
        pass

    with pytest.raises(RuntimeError, match=r"^from_url must be overriden$"):
        Problem.from_url("")
    del DummyProblem

    gc.collect()
    assert Problem.from_url("") is None
