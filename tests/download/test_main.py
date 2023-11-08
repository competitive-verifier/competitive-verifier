from typing import Iterable, Union

import pytest

from competitive_verifier.download.main import UrlOrVerificationFile, parse_urls
from competitive_verifier.models import ProblemVerification, VerificationFile


def get_problem_command(url: str) -> ProblemVerification:
    return ProblemVerification(command="true", problem=url)


_SomeUrlOrVerificationFile = Union[
    UrlOrVerificationFile, Iterable[UrlOrVerificationFile]
]
test_parse_urls_params: list[tuple[_SomeUrlOrVerificationFile, set[str]]] = [
    (
        "http://example.com",
        {
            "http://example.com",
        },
    ),
    (
        VerificationFile(
            verification=[
                get_problem_command("http://example.com/alpha"),
                get_problem_command("http://example.com/beta"),
                get_problem_command("http://example.com/gamma"),
                get_problem_command("http://example.com/delta"),
            ]
        ),
        {
            "http://example.com/alpha",
            "http://example.com/beta",
            "http://example.com/gamma",
            "http://example.com/delta",
        },
    ),
    (
        [
            VerificationFile(
                verification=[
                    get_problem_command("http://example.com/alpha"),
                    get_problem_command("http://example.com/beta"),
                    get_problem_command("http://example.com/gamma"),
                    get_problem_command("http://example.com/delta"),
                ]
            ),
            VerificationFile(
                verification=[
                    get_problem_command("https://example.com/alpha"),
                    get_problem_command("https://example.com/beta"),
                    get_problem_command("https://example.com/gamma"),
                    get_problem_command("https://example.com/delta"),
                ]
            ),
        ],
        {
            "http://example.com/alpha",
            "http://example.com/beta",
            "http://example.com/gamma",
            "http://example.com/delta",
            "https://example.com/alpha",
            "https://example.com/beta",
            "https://example.com/gamma",
            "https://example.com/delta",
        },
    ),
    (
        [
            VerificationFile(
                verification=[
                    get_problem_command("http://example.com/alpha"),
                    get_problem_command("http://example.com/beta"),
                    get_problem_command("http://example.com/gamma"),
                    get_problem_command("http://example.com/delta"),
                    get_problem_command("https://example.com/alpha"),
                ]
            ),
            "https://example.com/alpha",
            "https://example.com/beta",
            "https://example.com/beta",
            "https://example.com/gamma",
            "https://example.com/delta",
        ],
        {
            "http://example.com/alpha",
            "http://example.com/beta",
            "http://example.com/gamma",
            "http://example.com/delta",
            "https://example.com/alpha",
            "https://example.com/beta",
            "https://example.com/gamma",
            "https://example.com/delta",
        },
    ),
]


@pytest.mark.parametrize(
    "input, expected",
    test_parse_urls_params,
    ids=range(len(test_parse_urls_params)),
)
def test_parse_urls(
    input: _SomeUrlOrVerificationFile,
    expected: set[str],
):
    assert set(parse_urls(input)) == expected
