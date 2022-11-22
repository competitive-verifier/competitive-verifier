import argparse
import os
import pathlib
from typing import Any
from unittest import mock

import pytest

import competitive_verifier.oj as oj


@pytest.fixture
def clear_env():
    os.environ.clear()


def test_oj_download(clear_env: Any):
    with mock.patch(
        "competitive_verifier.oj.get_cache_directory",
        return_value=pathlib.Path("/bar/baz/online-judge-tools"),
    ), mock.patch.object(pathlib.Path, "mkdir") as mkdir, mock.patch(
        "onlinejudge_command.subcommand.download.run"
    ) as patch:
        oj.download("http://example.com")
        mkdir.assert_called_once()
        patch.assert_called_once()
        args = patch.call_args[0][0]

        assert isinstance(args, argparse.Namespace)
        assert args.subcommand == "download"
        assert args.cookie == pathlib.Path("/bar/baz/online-judge-tools") / "cookie.txt"
        assert args.url == "http://example.com"
        assert args.directory == pathlib.Path(
            ".competitive-verifier/cache/problems/a9b9f04336ce0181a08e774e01113b31/test"
        )
        assert args.yukicoder_token is None


def test_oj_download_yukicoder():
    with mock.patch(
        "competitive_verifier.oj.get_cache_directory",
        return_value=pathlib.Path("/bar/baz/online-judge-tools"),
    ), mock.patch.object(pathlib.Path, "mkdir") as mkdir, mock.patch(
        "onlinejudge_command.subcommand.download.run"
    ) as patch:
        try:
            os.environ["YUKICODER_TOKEN"] = "YKTK"
            oj.download("http://example.com")
            mkdir.assert_called_once()
            patch.assert_called_once()
            args = patch.call_args[0][0]

            assert isinstance(args, argparse.Namespace)
            assert args.subcommand == "download"
            assert (
                args.cookie
                == pathlib.Path("/bar/baz/online-judge-tools") / "cookie.txt"
            )
            assert args.url == "http://example.com"
            assert args.directory == pathlib.Path(
                ".competitive-verifier/cache/problems/a9b9f04336ce0181a08e774e01113b31/test"
            )
            assert args.yukicoder_token == "YKTK"
        finally:
            del os.environ["YUKICODER_TOKEN"]


def test_oj_test():
    with mock.patch(
        "competitive_verifier.oj.get_cache_directory",
        return_value=pathlib.Path("/bar/baz/online-judge-tools"),
    ), mock.patch("onlinejudge_command.subcommand.test.run") as patch:
        oj.test(url="http://example.com", command="ls .", tle=2, error=None)

        patch.assert_called_once()
        args = patch.call_args[0][0]

        assert isinstance(args, argparse.Namespace)
        assert args.subcommand == "test"
        assert args.print_input is True
        assert args.cookie == pathlib.Path("/bar/baz/online-judge-tools") / "cookie.txt"
        assert args.tle == 2.0
        assert args.error is None
        assert args.command == "ls ."
        assert args.directory == pathlib.Path(
            ".competitive-verifier/cache/problems/a9b9f04336ce0181a08e774e01113b31/test"
        )
