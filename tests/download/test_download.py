import contextlib
import os
import pathlib
from dataclasses import dataclass
from typing import Optional

import onlinejudge.service.atcoder as atcoder
import onlinejudge.service.library_checker as library_checker
import onlinejudge.service.yukicoder as yukicoder
import onlinejudge.type
import pytest
import requests
from pytest_mock import MockerFixture
from pytest_mock.plugin import MockType

from competitive_verifier.download.main import run_impl as download


@dataclass
class MockProblem:
    download_system_cases: MockType
    download_sample_cases: MockType
    generate_test_cases_in_cloned_repository: Optional[MockType] = None


@pytest.fixture
def mock_problem(mocker: MockerFixture, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.chdir(pathlib.Path(__file__).parent)
    mocker.patch.dict(
        os.environ, {"YUKICODER_TOKEN": "YKTK", "DROPBOX_TOKEN": "DBTK"}, clear=True
    )
    mocker.patch(
        "competitive_verifier.oj.tools.test_command.get_cache_directory",
        return_value=pathlib.Path("/bar/baz/online-judge-tools"),
    )
    mocker.patch(
        "competitive_verifier.oj.tools.download_command.get_checker_path",
        return_value=None,
    )

    @contextlib.contextmanager
    def new_session_with_our_user_agent(*, path: pathlib.Path):
        sess = requests.Session()
        sess.headers = {}
        yield sess

    mocker.patch(
        "competitive_verifier.oj.tools.utils.new_session_with_our_user_agent",
        side_effect=new_session_with_our_user_agent,
    )

    return {
        problem_type: MockProblem(
            download_system_cases=mocker.patch.object(
                problem_type,
                "download_system_cases",
                return_value=[],
            ),
            download_sample_cases=mocker.patch.object(
                problem_type,
                "download_sample_cases",
                return_value=[],
            ),
        )
        for problem_type in [
            yukicoder.YukicoderProblem,
            atcoder.AtCoderProblem,
        ]
    } | {
        library_checker.LibraryCheckerProblem: MockProblem(
            download_system_cases=mocker.patch.object(
                library_checker.LibraryCheckerProblem,
                "download_system_cases",
                return_value=[],
            ),
            download_sample_cases=mocker.patch.object(
                library_checker.LibraryCheckerProblem,
                "download_sample_cases",
                return_value=[],
            ),
            generate_test_cases_in_cloned_repository=mocker.patch.object(
                library_checker.LibraryCheckerProblem,
                "_generate_test_cases_in_cloned_repository",
                return_value=None,
            ),
        )
    }


@pytest.fixture
def mkdir(mocker: MockerFixture):
    return mocker.patch.object(pathlib.Path, "mkdir", autospec=True)


def test_oj_download(
    mkdir: MockType,
    mock_problem: dict[type[onlinejudge.type.Problem], MockProblem],
):
    download(
        input=[
            "https://judge.yosupo.jp/problem/aplusb",
            "https://judge.yosupo.jp/problem/aplusb",
            "https://yukicoder.me/problems/no/1088",
            "https://atcoder.jp/contests/abc322/tasks/abc322_a",
        ]
    )

    assert mkdir.call_count == 3
    assert sorted(call[0][0] for call in mkdir.call_args_list) == [
        pathlib.Path(
            ".competitive-verifier/cache/problems/84d0ff7b028fc0f8cf7973b22fee1634"
        ),
        pathlib.Path(
            ".competitive-verifier/cache/problems/8e3916c7805235eb07ec2a58660d89c6"
        ),
        pathlib.Path(
            ".competitive-verifier/cache/problems/9b6d910460fc44fca27d05f01d26c882"
        ),
    ]

    assert set(mock_problem.keys()) == {
        library_checker.LibraryCheckerProblem,
        yukicoder.YukicoderProblem,
        atcoder.AtCoderProblem,
    }

    #
    mock_library_checker = mock_problem[library_checker.LibraryCheckerProblem]
    mock_library_checker.download_sample_cases.assert_not_called()
    mock_library_checker.download_system_cases.assert_not_called()
    mock_library_checker.generate_test_cases_in_cloned_repository.assert_called_once()  # type: ignore

    mock_yuki_coder = mock_problem[yukicoder.YukicoderProblem]
    mock_yuki_coder.download_sample_cases.assert_not_called()
    mock_yuki_coder.download_system_cases.assert_called_once()
    assert mock_yuki_coder.download_system_cases.call_args[1]["session"].headers == {
        "Authorization": "Bearer YKTK"
    }

    mock_at_coder = mock_problem[atcoder.AtCoderProblem]
    mock_at_coder.download_sample_cases.assert_not_called()
    mock_at_coder.download_system_cases.assert_called_once()
    assert mock_at_coder.download_system_cases.call_args[1]["session"].headers == {
        "Authorization": "Bearer DBTK"
    }
