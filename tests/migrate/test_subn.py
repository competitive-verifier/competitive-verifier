import textwrap

import pytest

from competitive_verifier.migrate.migration import problem_subn

test_problem_subn_params = {
    "NO PROBLEM": (
        textwrap.dedent(
            """
        #define PROGRAM 2
        void main() { }"""
        ),
        (
            textwrap.dedent(
                """
        #define PROGRAM 2
        void main() { }"""
            ),
            0,
        ),
    ),
    "PROBLEM": (
        textwrap.dedent(
            """
        #define PROBLEM http://example.com
        void main() { }"""
        ),
        (
            textwrap.dedent(
                """
        // competitive-verifier: PROBLEM http://example.com
        void main() { }"""
            ),
            1,
        ),
    ),
    "BACKSLASH BREAK": (
        textwrap.dedent(
            r"""
        #define PROBLEM \
           http://example.com
        void main() { }"""
        ),
        (
            textwrap.dedent(
                """
        // competitive-verifier: PROBLEM http://example.com
        void main() { }"""
            ),
            1,
        ),
    ),
    "QUOTE PROBLEM": (
        textwrap.dedent(
            """
        #define PROBLEM "http://example.com"
        void main() { }"""
        ),
        (
            textwrap.dedent(
                """
        // competitive-verifier: PROBLEM http://example.com
        void main() { }"""
            ),
            1,
        ),
    ),
    "QUOTE BACKSLASH BREAK": (
        textwrap.dedent(
            r"""
        #define PROBLEM \
           "http://example.com"
        void main() { }"""
        ),
        (
            textwrap.dedent(
                """
        // competitive-verifier: PROBLEM http://example.com
        void main() { }"""
            ),
            1,
        ),
    ),
    "NO BACKSLASH PROBLEM": (
        textwrap.dedent(
            """
        #define PROBLEM
        // http://example.com
        void main() { }"""
        ),
        (
            textwrap.dedent(
                """
        #define PROBLEM
        // http://example.com
        void main() { }"""
            ),
            0,
        ),
    ),
}


@pytest.mark.parametrize(
    "content, expected",
    test_problem_subn_params.values(),
    ids=test_problem_subn_params.keys(),
)
def test_problem_subn(content: str, expected: tuple[str, int]):
    assert problem_subn(content) == expected
