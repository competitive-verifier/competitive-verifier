import os
import sys
from io import StringIO

import pytest
from pytest_mock import MockerFixture

from competitive_verifier import github
from competitive_verifier.log import group


class TestGitHubPrint:
    def test_print_error(
        self,
        capsys: pytest.CaptureFixture[str],
        mocker: MockerFixture,
    ):
        mocker.patch.dict(os.environ, {"GITHUB_ACTIONS": ""}, clear=True)
        github.print_error("simple_message")
        out, err = capsys.readouterr()
        assert out == ""
        assert err == ""

        github.print_error("simple_message", force=True)
        out, err = capsys.readouterr()
        assert out == "::error ::simple_message\n"
        assert err == ""

    def test_print_error_github_actions(
        self,
        capsys: pytest.CaptureFixture[str],
        mocker: MockerFixture,
    ):
        mocker.patch.dict(os.environ, {"GITHUB_ACTIONS": "true"}, clear=True)
        github.print_error(
            "many_message",
            title="TestTitle",
            file="foo.txt",
            col=10,
            end_column=20,
            line=100,
            end_line=101,
            stream=sys.stderr,
            force=True,
        )
        out, err = capsys.readouterr()
        assert out == ""
        assert (
            err
            == "::error title=TestTitle,file=foo.txt,col=10,endColumn=20,line=100,endLine=101::many_message\n"
        )


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

    def test_log_group_console(
        self, capsys: pytest.CaptureFixture[str], mocker: MockerFixture
    ):
        mocker.patch.dict(os.environ, {"GITHUB_ACTIONS": ""}, clear=True)
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

    def test_log_group_console_stream(self, mocker: MockerFixture):
        mocker.patch.dict(os.environ, {"GITHUB_ACTIONS": ""}, clear=True)
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
