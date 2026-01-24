import os
from io import StringIO

import pytest
from pytest_mock import MockerFixture

from competitive_verifier.log import group


class TestLogGroup:
    def test_log_group_github_actions(
        self, mocker: MockerFixture, capsys: pytest.CaptureFixture[str]
    ):
        mocker.patch.dict(os.environ, {"GITHUB_ACTIONS": "true"}, clear=True)
        with group("TestTitle"):
            out, err = capsys.readouterr()
            assert out == ""
            assert err == "::group::TestTitle\n"

        out, err = capsys.readouterr()
        assert out == ""
        assert err == "::endgroup::\n"

    def test_log_group_github_actions_stream(self, mocker: MockerFixture):
        mocker.patch.dict(os.environ, {"GITHUB_ACTIONS": "true"}, clear=True)
        with StringIO() as fp:
            with group("TestTitle", stream=fp):
                fp.seek(0)
                assert fp.read() == "::group::TestTitle\n"
                fp.seek(0)
                fp.truncate(0)
            fp.seek(0)
            assert fp.read() == "::endgroup::\n"

    def test_log_group_console(self, capsys: pytest.CaptureFixture[str]):
        with group("TestTitle"):
            out, err = capsys.readouterr()
            assert out == ""
            assert (
                err
                == "<------------- \x1b[36m Start group:\x1b[33mTestTitle\x1b[0m ------------->\n"
            )

        out, err = capsys.readouterr()
        assert out == ""
        assert (
            err
            == "<------------- \x1b[36mFinish group:\x1b[33mTestTitle\x1b[0m ------------->\n"
        )

    def test_log_group_console_stream(self):
        with StringIO() as fp:
            with group("TestTitle", stream=fp):
                fp.seek(0)
                assert (
                    fp.read()
                    == "<------------- \x1b[36m Start group:\x1b[33mTestTitle\x1b[0m ------------->\n"
                )
                fp.seek(0)
                fp.truncate(0)
            fp.seek(0)
            assert (
                fp.read()
                == "<------------- \x1b[36mFinish group:\x1b[33mTestTitle\x1b[0m ------------->\n"
            )
