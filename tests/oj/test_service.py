import pytest

from competitive_verifier.oj.tools.service.text import normpath

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
