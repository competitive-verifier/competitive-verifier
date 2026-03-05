import logging

import pytest
from pytest_mock import MockerFixture

from competitive_verifier import oj
from competitive_verifier.log import GitHubMessageParams
from competitive_verifier.oj.problem import NotLoggedInError, YukicoderProblem
from tests import LogComparer


def test_oj_download_not_supported(caplog: pytest.LogCaptureFixture):
    caplog.set_level(logging.NOTSET)
    assert oj.download("https://example.com/notfound") is False
    assert caplog.records == [
        LogComparer(
            'The URL "https://example.com/notfound" is not supported',
            logging.ERROR,
            github=GitHubMessageParams(),
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
    assert caplog.records == [
        LogComparer(
            "download[Run]: https://yukicoder.me/problems/no/499",
            logging.INFO,
        ),
        LogComparer(
            "Login is required to download the problem. "
            "'https://yukicoder.me/problems/no/499'",
            logging.ERROR,
            github=GitHubMessageParams(),
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
    assert caplog.records == [
        LogComparer(
            "download[Run]: https://yukicoder.me/problems/no/499",
            logging.INFO,
        ),
        LogComparer(
            "Failed to download. 'https://yukicoder.me/problems/no/499'",
            logging.ERROR,
            github=GitHubMessageParams(),
        ),
    ]
