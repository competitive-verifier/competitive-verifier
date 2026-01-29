import os
import pathlib
from dataclasses import dataclass

import pytest
from pytest_mock import MockerFixture
from pytest_mock.plugin import MockType

from competitive_verifier.download import download_files as download
from competitive_verifier.oj.tools import service


@dataclass
class MockProblem:
    download_system_cases: MockType
    generate_test_cases_in_cloned_repository: MockType | None = None


@pytest.fixture
def mock_problem(mocker: MockerFixture, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.chdir(pathlib.Path(__file__).parent)
    mocker.patch.dict(os.environ, {"YUKICODER_TOKEN": "YKTK"}, clear=True)
    mocker.patch(
        "competitive_verifier.oj.tools.oj_download.get_checker_path",
        return_value=None,
    )

    return {
        service.YukicoderProblem: MockProblem(
            download_system_cases=mocker.patch.object(
                service.YukicoderProblem,
                "download_system_cases",
                return_value=[],
            ),
        ),
        service.LibraryCheckerProblem: MockProblem(
            download_system_cases=mocker.patch.object(
                service.LibraryCheckerProblem,
                "download_system_cases",
                return_value=[],
            ),
            generate_test_cases_in_cloned_repository=mocker.patch.object(
                service.LibraryCheckerProblem,
                "generate_test_cases_in_cloned_repository",
                return_value=None,
            ),
        ),
    }


def test_oj_download(
    mocker: MockerFixture, mock_problem: dict[type[service.Problem], MockProblem]
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
        service.LibraryCheckerProblem,
        service.YukicoderProblem,
    }

    mock_library_checker = mock_problem[service.LibraryCheckerProblem]
    mock_library_checker.download_system_cases.assert_not_called()
    assert mock_library_checker.generate_test_cases_in_cloned_repository
    mock_library_checker.generate_test_cases_in_cloned_repository.assert_called_once()

    mock_yuki_coder = mock_problem[service.YukicoderProblem]
    mock_yuki_coder.download_system_cases.assert_called_once_with()
