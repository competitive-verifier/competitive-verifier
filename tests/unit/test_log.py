import logging
import os
import sys
from io import StringIO

import pytest
from pytest_mock import MockerFixture

from competitive_verifier.log import GitHubActionsHandler, GitHubMessageParams, group

test_github_actions_handler_params = []


def test_github_actions_handler(capsys: pytest.CaptureFixture[str]):
    handler = GitHubActionsHandler(stream=sys.stderr)

    def getLogger(name: str):
        logger = logging.getLogger(name)
        logger.addHandler(handler)
        logger.setLevel(1)
        return logger

    GitHub = "GitHub"
    logger = getLogger("competitive_verifier.handler")

    logger.log(1, "Super low", extra={"github": GitHubMessageParams()})
    logger.debug("DebugLog")
    logger.debug("%sDebugLog\nFin", GitHub, extra={"github": GitHubMessageParams()})
    out, err = capsys.readouterr()
    assert out == ""
    assert err == "::debug::DebugLog\n::debug::GitHubDebugLog\\nFin\n"

    logger.info("InfoLog")
    logger.info("%sInfoLog\nFin", GitHub, extra={"github": GitHubMessageParams()})
    out, err = capsys.readouterr()
    assert out == ""
    assert err == "::notice ::GitHubInfoLog\\nFin\n"

    logger.warning("WarningLog")
    logger.warning("%sWarningLog\nFin", GitHub, extra={"github": GitHubMessageParams()})
    out, err = capsys.readouterr()
    assert out == ""
    assert err == "::warning ::GitHubWarningLog\\nFin\n"

    logger.exception("ErrorLog")
    logger.error(
        "%sErrorLog\nFin",
        GitHub,
        extra={
            "github": GitHubMessageParams(
                title="TestTitle",
                file="foo.txt",
                col=10,
                end_column=20,
                line=100,
                end_line=101,
            )
        },
    )
    out, err = capsys.readouterr()
    assert out == ""
    assert (
        err
        == "::error title=TestTitle,file=foo.txt,col=10,endColumn=20,line=100,endLine=101::GitHubErrorLog\\nFin\n"
    )

    logger2 = getLogger("otherlib.handler")
    logger2.error("%sErrorLog\nFin", GitHub, extra={"github": GitHubMessageParams()})
    out, err = capsys.readouterr()
    assert out == ""
    assert err == "::error title=otherlib.handler::GitHubErrorLog\\nFin\n"

    logger2 = getLogger("otherlib.handler")
    logger2.error("%sErrorLog\nFin", GitHub, extra={"github": GitHubMessageParams()})
    out, err = capsys.readouterr()
    assert out == ""
    assert err == "::error title=otherlib.handler::GitHubErrorLog\\nFin\n"


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
