import os
import pathlib

import pytest
from pytest_mock import MockerFixture
from pytest_mock.plugin import MockType

from competitive_verifier.download import download_files as download
from competitive_verifier.oj import problem


@pytest.fixture
def mock_problem(mocker: MockerFixture, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.chdir(pathlib.Path(__file__).parent)
    mocker.patch.dict(os.environ, {"YUKICODER_TOKEN": "YKTK"}, clear=True)

    return {
        problem.YukicoderProblem: mocker.patch.object(
            problem.YukicoderProblem,
            "download_system_cases",
            return_value=[],
        ),
        problem.LibraryCheckerProblem: mocker.patch.object(
            problem.LibraryCheckerProblem,
            "download_system_cases",
            return_value=[],
        ),
    }


def test_oj_download(mock_problem: dict[type[problem.Problem], MockType]):
    download(
        url_or_file=[
            "https://judge.yosupo.jp/problem/aplusb",
            "https://judge.yosupo.jp/problem/aplusb",
            "https://yukicoder.me/problems/no/1088",
        ]
    )

    assert set(mock_problem.keys()) == {
        problem.LibraryCheckerProblem,
        problem.YukicoderProblem,
    }

    mock_library_checker = mock_problem[problem.LibraryCheckerProblem]
    mock_library_checker.assert_called_once_with()

    mock_yuki_coder = mock_problem[problem.YukicoderProblem]
    mock_yuki_coder.assert_called_once_with()
