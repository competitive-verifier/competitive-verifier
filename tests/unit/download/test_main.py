import logging
import pathlib
from collections.abc import Iterable

import pytest
from pytest_mock import MockerFixture

from competitive_verifier.download.download import (
    Download,
    UrlOrVerificationFile,
    parse_urls,
)
from competitive_verifier.models import (
    ProblemVerification,
    VerificationFile,
    VerificationInput,
)
from tests import LogComparer


def get_problem_command(url: str) -> ProblemVerification:
    return ProblemVerification(command="true", problem=url)


_SomeUrlOrVerificationFile = UrlOrVerificationFile | Iterable[UrlOrVerificationFile]
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
    ("url_or_file", "expected"),
    test_parse_urls_params,
)
def test_parse_urls(
    url_or_file: _SomeUrlOrVerificationFile,
    expected: set[str],
):
    assert set(parse_urls(url_or_file)) == expected


test_download_run_params: list[
    tuple[list[str], VerificationInput | None, list[str | VerificationFile]]
] = [
    ([], None, []),
    (
        [
            "https://example.com/alpha",
            "https://example.com/beta",
            "https://example.com/beta",
            "https://example.com/gamma",
            "https://example.com/delta",
        ],
        None,
        [
            "https://example.com/alpha",
            "https://example.com/beta",
            "https://example.com/beta",
            "https://example.com/gamma",
            "https://example.com/delta",
        ],
    ),
    (
        [],
        VerificationInput(
            files={
                pathlib.Path("foo.py"): VerificationFile(
                    verification=[
                        get_problem_command("http://example.com/alpha"),
                        get_problem_command("http://example.com/beta"),
                        get_problem_command("http://example.com/gamma"),
                        get_problem_command("http://example.com/delta"),
                        get_problem_command("https://example.com/alpha"),
                    ]
                ),
            }
        ),
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
        ],
    ),
    (
        [
            "https://example.com/kilo",
            "https://example.com/mega",
            "https://example.com/giga",
            "https://example.com/tera",
        ],
        VerificationInput(
            files={
                pathlib.Path("foo.py"): VerificationFile(
                    verification=[
                        get_problem_command("http://example.com/alpha"),
                        get_problem_command("http://example.com/beta"),
                        get_problem_command("http://example.com/gamma"),
                        get_problem_command("http://example.com/delta"),
                        get_problem_command("https://example.com/alpha"),
                    ]
                ),
            }
        ),
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
            "https://example.com/kilo",
            "https://example.com/mega",
            "https://example.com/giga",
            "https://example.com/tera",
        ],
    ),
]


@pytest.mark.parametrize(
    ("urls", "verification_input", "expected"),
    test_download_run_params,
)
def test_download_run(
    urls: list[str],
    verification_input: VerificationInput | None,
    expected: list[str | VerificationFile],
    caplog: pytest.LogCaptureFixture,
    mocker: MockerFixture,
    testtemp: pathlib.Path,
):
    caplog.set_level(0)
    mock_download_files = mocker.patch(
        "competitive_verifier.download.download.download_files"
    )

    verify_files_json = None
    if verification_input:
        (verify_files_json := testtemp / "verify.json").write_text(
            verification_input.model_dump_json()
        )

    assert Download(urls=urls, verify_files_json=verify_files_json).run()

    mock_download_files.assert_called_once_with(expected, group_log=True)
    assert caplog.records == [
        LogComparer(
            f"arguments:{Download(urls=urls, verify_files_json=verify_files_json)}",
            logging.DEBUG,
        ),
        LogComparer(
            f"verify_files_json={verify_files_json}, urls={urls}",
            logging.INFO,
        ),
    ]
