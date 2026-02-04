import logging
import os
import sys
from typing import Any

import pytest
from pytest_mock import MockerFixture

from competitive_verifier.exec import exec_command


def test_exec_group_log(
    capsys: pytest.CaptureFixture[str],
    caplog: pytest.LogCaptureFixture,
    mocker: MockerFixture,
):
    def mockrun(command: Any, **kwargs: dict[str, Any]):
        print("mockrun", file=sys.stderr)  # noqa: T201

    mocker.patch.dict(os.environ, {"GITHUB_ACTIONS": "true"}, clear=True)
    mocker.patch("subprocess.run", side_effect=mockrun)

    exec_command("echo 1", group_log=True)

    assert len(caplog.record_tuples) == 0
    out, err = capsys.readouterr()
    assert out == ""
    assert err == "::group::subprocess.run: echo 1\nmockrun\n::endgroup::\n"


def test_exec_not_group_log(
    capsys: pytest.CaptureFixture[str],
    caplog: pytest.LogCaptureFixture,
    mocker: MockerFixture,
):
    def mockrun(command: Any, **kwargs: dict[str, Any]):
        logging.getLogger("test").error("mockrun")

    mocker.patch.dict(os.environ, {"GITHUB_ACTIONS": "true"}, clear=True)
    mocker.patch("subprocess.run", side_effect=mockrun)
    caplog.set_level(logging.NOTSET)

    exec_command("echo 1")

    assert caplog.record_tuples == [
        ("competitive_verifier.exec", logging.INFO, "subprocess.run: echo 1"),
        ("test", logging.ERROR, "mockrun"),
    ]
    out, err = capsys.readouterr()
    assert out == ""
    assert err == ""
