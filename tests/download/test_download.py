import contextlib
import os
import pathlib
from typing import Any, TypedDict

import onlinejudge.service.atcoder as atcoder
import onlinejudge.service.library_checker as library_checker
import onlinejudge.service.yukicoder as yukicoder
import onlinejudge.type
import pytest
import requests
from pytest_mock import MockerFixture
from pytest_mock.plugin import MockType

from competitive_verifier.download.main import run_impl as download


class MockProblem(TypedDict):
    download_system_cases: MockType
    download_sample_cases: MockType


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
        "onlinejudge_command.utils.new_session_with_our_user_agent",
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
            library_checker.LibraryCheckerProblem,
            yukicoder.YukicoderProblem,
            atcoder.AtCoderProblem,
        ]
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
            "https://yukicoder.me/problems/no/3040",
            "https://atcoder.jp/contests/abc322/tasks/abc322_a",
        ]
    )

    assert mkdir.call_count == 3
    assert sorted(call[0][0] for call in mkdir.call_args_list) == [
        pathlib.Path(
            ".competitive-verifier/cache/problems/20c21841818196666af22f1bfb3dbd3e"
        ),
        pathlib.Path(
            ".competitive-verifier/cache/problems/84d0ff7b028fc0f8cf7973b22fee1634"
        ),
        pathlib.Path(
            ".competitive-verifier/cache/problems/8e3916c7805235eb07ec2a58660d89c6"
        ),
    ]

    for m in mock_problem.values():
        m["download_sample_cases"].assert_not_called()
        m["download_system_cases"].assert_called_once()

    class SessionData(TypedDict):
        headers: dict[str, Any]
        cookies: dict[str, Any]

    calls: dict[type[onlinejudge.type.Problem], SessionData] = {
        k: {
            "headers": v["download_system_cases"].call_args[1]["session"].headers,
            "cookies": v["download_system_cases"]
            .call_args[1]["session"]
            .cookies.get_dict(),
        }
        for k, v in mock_problem.items()
    }

    assert calls == {
        library_checker.LibraryCheckerProblem: {"headers": {}, "cookies": {}},
        yukicoder.YukicoderProblem: {
            "headers": {"Authorization": "Bearer YKTK"},
            "cookies": {},
        },
        atcoder.AtCoderProblem: {
            "headers": {"Authorization": "Bearer DBTK"},
            "cookies": {},
        },
    }
