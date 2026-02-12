import logging

import pytest
from pytest_mock import MockerFixture

from competitive_verifier import oj
from competitive_verifier.oj.problem import NotLoggedInError, YukicoderProblem


def test_oj_download_not_supported(caplog: pytest.LogCaptureFixture):
    caplog.set_level(logging.NOTSET)
    assert oj.download("https://example.com/notfound") is False
    assert caplog.record_tuples == [
        (
            "competitive_verifier.oj.oj_download",
            logging.ERROR,
            'The URL "https://example.com/notfound" is not supported',
        ),
    ]


def test_oj_download_not_logged_in(
    mocker: MockerFixture,
    caplog: pytest.LogCaptureFixture,
):
    caplog.set_level(logging.NOTSET)
    mocker.patch.object(
        YukicoderProblem,
        "download_system_cases",
        side_effect=NotLoggedInError("test error"),
    )

    assert oj.download("https://yukicoder.me/problems/no/499") is False
    assert caplog.record_tuples == [
        (
            "competitive_verifier.oj.oj_download",
            logging.INFO,
            "download[Run]: https://yukicoder.me/problems/no/499",
        ),
        (
            "competitive_verifier.oj.oj_download",
            logging.ERROR,
            "Login is required to download the problem. "
            "'https://yukicoder.me/problems/no/499'",
        ),
    ]


def test_oj_download_error(
    mocker: MockerFixture,
    caplog: pytest.LogCaptureFixture,
):
    caplog.set_level(logging.NOTSET)
    mocker.patch.object(
        YukicoderProblem,
        "download_system_cases",
        side_effect=RuntimeError("test error"),
    )

    assert oj.download("https://yukicoder.me/problems/no/499") is False
    assert caplog.record_tuples == [
        (
            "competitive_verifier.oj.oj_download",
            logging.INFO,
            "download[Run]: https://yukicoder.me/problems/no/499",
        ),
        (
            "competitive_verifier.oj.oj_download",
            logging.ERROR,
            "Failed to download. 'https://yukicoder.me/problems/no/499'",
        ),
    ]
