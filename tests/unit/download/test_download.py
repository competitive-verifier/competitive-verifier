import os
import pathlib

import pytest
from pytest_mock import MockerFixture
from pytest_mock.plugin import MockType

from competitive_verifier.download import download_files as download
from competitive_verifier.oj.tools import problem


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


def test_oj_download(
    mocker: MockerFixture, mock_problem: dict[type[problem.Problem], MockType]
):
    mkdir = mocker.patch.object(pathlib.Path, "mkdir", autospec=True)

    download(
        url_or_file=[
            "https://judge.yosupo.jp/problem/aplusb",
            "https://judge.yosupo.jp/problem/aplusb",
            "https://yukicoder.me/problems/no/1088",
        ]
    )

    assert mkdir.call_count == 2
    assert sorted(call[0][0] for call in mkdir.call_args_list) == [
        pathlib.Path(
            ".competitive-verifier/cache/problems/8e3916c7805235eb07ec2a58660d89c6"
        ),
        pathlib.Path(
            ".competitive-verifier/cache/problems/9b6d910460fc44fca27d05f01d26c882"
        ),
    ]

    assert set(mock_problem.keys()) == {
        problem.LibraryCheckerProblem,
        problem.YukicoderProblem,
    }

    mock_library_checker = mock_problem[problem.LibraryCheckerProblem]
    mock_library_checker.assert_called_once_with()

    mock_yuki_coder = mock_problem[problem.YukicoderProblem]
    mock_yuki_coder.assert_called_once_with()
