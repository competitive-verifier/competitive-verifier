import argparse
import contextlib
import os
import pathlib
from typing import Any

import pytest
import requests
from pytest_mock import MockerFixture
from pytest_mock.plugin import MockType

import competitive_verifier.oj as oj


@pytest.fixture
def setenv(mocker: MockerFixture):
    mocker.patch.dict(
        os.environ, {"YUKICODER_TOKEN": "YKTK", "DROPBOX_TOKEN": "DBTK"}, clear=True
    )
    mocker.patch(
        "competitive_verifier.oj.get_cache_directory",
        return_value=pathlib.Path("/bar/baz/online-judge-tools"),
    )
    mocker.patch(
        "competitive_verifier.oj.get_checker_path",
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


@pytest.fixture
def mkdir(mocker: MockerFixture):
    return mocker.patch.object(pathlib.Path, "mkdir")


def test_oj_download(mocker: MockerFixture, mkdir: MockType, setenv: Any):
    import onlinejudge.service.library_checker as service

    download_system_cases: MockType = mocker.patch.object(
        service.LibraryCheckerProblem,
        "download_system_cases",
        return_value=[],
    )
    download_sample_cases = mocker.patch.object(
        service.LibraryCheckerProblem,
        "download_sample_cases",
        return_value=[],
    )

    oj.download("https://judge.yosupo.jp/problem/aplusb")

    mkdir.assert_called_once()
    download_sample_cases.assert_not_called()
    download_system_cases.assert_called_once()

    sess: requests.Session = download_system_cases.call_args[1]["session"]
    cookies = (  # pyright: ignore[ reportUnknownVariableType]
        sess.cookies.get_dict()  # pyright: ignore[reportUnknownMemberType]
    )
    assert cookies == {}

    headers = (  # pyright: ignore[ reportUnknownVariableType]
        sess.headers  # pyright: ignore[reportUnknownMemberType]
    )
    assert headers == {}


def test_oj_download_yukicoder(mocker: MockerFixture, mkdir: MockType, setenv: Any):
    import onlinejudge.service.yukicoder as service

    download_system_cases: MockType = mocker.patch.object(
        service.YukicoderProblem,
        "download_system_cases",
        return_value=[],
    )
    download_sample_cases = mocker.patch.object(
        service.YukicoderProblem,
        "download_sample_cases",
        return_value=[],
    )

    oj.download("https://yukicoder.me/problems/no/3040")

    mkdir.assert_called_once()
    download_sample_cases.assert_not_called()
    download_system_cases.assert_called_once()

    sess: requests.Session = download_system_cases.call_args[1]["session"]
    cookies = (  # pyright: ignore[ reportUnknownVariableType]
        sess.cookies.get_dict()  # pyright: ignore[reportUnknownMemberType]
    )
    assert cookies == {}

    headers = (  # pyright: ignore[ reportUnknownVariableType]
        sess.headers  # pyright: ignore[reportUnknownMemberType]
    )
    assert headers == {"Authorization": "Bearer YKTK"}


def test_oj_download_atcoder(mocker: MockerFixture, mkdir: MockType, setenv: Any):
    import onlinejudge.service.atcoder as service

    download_system_cases: MockType = mocker.patch.object(
        service.AtCoderProblem,
        "download_system_cases",
        return_value=[],
    )
    download_sample_cases = mocker.patch.object(
        service.AtCoderProblem,
        "download_sample_cases",
        return_value=[],
    )

    oj.download("https://atcoder.jp/contests/abc322/tasks/abc322_a")

    mkdir.assert_called_once()
    download_sample_cases.assert_not_called()
    download_system_cases.assert_called_once()

    sess: requests.Session = download_system_cases.call_args[1]["session"]
    cookies = (  # pyright: ignore[ reportUnknownVariableType]
        sess.cookies.get_dict()  # pyright: ignore[reportUnknownMemberType]
    )
    assert cookies == {}

    headers = (  # pyright: ignore[ reportUnknownVariableType]
        sess.headers  # pyright: ignore[reportUnknownMemberType]
    )
    assert headers == {"Authorization": "Bearer DBTK"}


def test_oj_test(mocker: MockerFixture, setenv: Any):
    run = mocker.patch("competitive_verifier.oj.run_test")

    oj.test(url="http://example.com", command="ls .", tle=2, error=None, mle=128)

    run.assert_called_once()
    args = run.call_args[0][0]

    assert isinstance(args, argparse.Namespace)
    assert args.subcommand == "test"
    assert args.print_input is True
    assert args.cookie == pathlib.Path("/bar/baz/online-judge-tools") / "cookie.txt"
    assert args.tle == 2.0
    assert args.mle == 128.0
    assert args.error is None
    assert args.command == "ls ."
    assert args.directory == pathlib.Path(
        ".competitive-verifier/cache/problems/a9b9f04336ce0181a08e774e01113b31/test"
    )
