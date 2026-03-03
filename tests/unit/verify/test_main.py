import logging
import os
import pathlib
import re
from datetime import datetime, timedelta, timezone

import pytest
from pytest_mock import MockerFixture

from competitive_verifier import app
from competitive_verifier.models import (
    FileResult,
    ResultStatus,
    VerificationResult,
    VerifyCommandResult,
)
from competitive_verifier.verify import Verify
from competitive_verifier.verify.verifier import SplitState
from tests import LogComparer

test_get_split_state_params = [
    (None, None, None),
    (5, 0, SplitState(size=5, index=0)),
    (5, 1, SplitState(size=5, index=1)),
    (5, 2, SplitState(size=5, index=2)),
    (5, 3, SplitState(size=5, index=3)),
    (5, 4, SplitState(size=5, index=4)),
]


@pytest.mark.parametrize(
    ("size", "index", "expected"),
    test_get_split_state_params,
    ids=str,
)
def test_get_split_state(
    size: int | None,
    index: int | None,
    expected: SplitState | None,
):
    v = Verify(
        subcommand="verify",
        verify_files_json=pathlib.Path("verify.json"),
        split=size,
        split_index=index,
    )
    assert v.split_state == expected


test_get_split_state_error_params = {
    "No split index": (
        ["--verify-json", "verify.json", "--split", "2"],
        "--split argument requires --split-index argument.",
    ),
    "No split": (
        ["--verify-json", "verify.json", "--split-index", "2"],
        "--split-index argument requires --split argument.",
    ),
    "split index": (
        ["--verify-json", "verify.json", "--split-index", "5", "--split", "5"],
        "--split-index must be greater than 0 and less than --split.",
    ),
    "split index negative": (
        ["--verify-json", "verify.json", "--split-index", "-1", "--split", "5"],
        "--split-index must be greater than 0 and less than --split.",
    ),
    "split zero": (
        ["--verify-json", "verify.json", "--split-index", "1", "--split", "0"],
        "--split must be greater than 0.",
    ),
}


@pytest.mark.parametrize(
    ("args", "message"),
    test_get_split_state_error_params.values(),
    ids=test_get_split_state_error_params.keys(),
)
def test_get_split_state_error(args: list[str], message: str):
    parsed = app.ArgumentParser().parse(["verify", *args])

    assert isinstance(parsed, app.Verify)

    with pytest.raises(ValueError, match=rf"^{re.escape(message)}$"):
        _ = parsed.split_state


def test_invalid_prev_result(
    monkeypatch: pytest.MonkeyPatch,
    testtemp: pathlib.Path,
    caplog: pytest.LogCaptureFixture,
):
    monkeypatch.chdir(testtemp)
    (testtemp / "prev.json").write_bytes(b'[1,2,3,"invalid"]')
    parsed = app.ArgumentParser().parse(
        [
            "verify",
            "--verify-json",
            "verify.json",
            "--prev-result",
            str(testtemp / "prev.json"),
        ]
    )
    assert isinstance(parsed, app.Verify)

    assert parsed.read_prev_result() is None

    assert caplog.records == [
        LogComparer(
            "Failed to parse prev_result: " + str(testtemp / "prev.json"),
            logging.WARNING,
        )
    ]


@pytest.mark.allow_mkdir
@pytest.mark.parametrize("output", [True, False])
def test_write_result_output(
    output: bool,
    monkeypatch: pytest.MonkeyPatch,
    mocker: MockerFixture,
    testtemp: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
):
    monkeypatch.chdir(testtemp)
    mocker.patch.dict(
        os.environ, {"GITHUB_STEP_SUMMARY": str(testtemp / "summary.md")}, clear=True
    )
    parsed = app.ArgumentParser().parse(
        [
            "verify",
            "--write-summary",
            "--verify-json",
            "verify.json",
            *(["--output", "result.json"] if output else []),
        ]
    )
    assert isinstance(parsed, app.Verify)
    parsed.write_result(
        VerifyCommandResult(
            total_seconds=5e-5,
            files={
                pathlib.Path("lib.c"): FileResult(
                    verifications=[
                        VerificationResult(
                            status=ResultStatus.SKIPPED,
                            elapsed=5e-6,
                            last_execution_time=datetime(
                                2021, 2, 28, 9, 17, tzinfo=timezone(timedelta(hours=9))
                            ),
                        )
                    ],
                )
            },
        )
    )
    expected = """{"total_seconds":0.00005,"files":{"lib.c":{"verifications":[{"status":"skipped","elapsed":5e-6,"last_execution_time":"2021-02-28T09:17:00+09:00"}],"newest":true}}}"""
    out, err = capsys.readouterr()
    assert out.strip() == expected
    assert err == ""

    if output:
        assert (testtemp / "result.json").read_text("utf-8") == expected
    else:
        assert not (testtemp / "result.json").exists()

    assert (
        (testtemp / "summary.md").read_text("utf-8")
        == """# ⚠ Verification result

- ✔&nbsp;&nbsp;All test case results are `success`
- ❌&nbsp;&nbsp;Test case results containts `failure`
- ⚠&nbsp;&nbsp;Test case results containts `skipped`


## Results
|📝&nbsp;&nbsp;File|✔<br>Passed|❌<br>Failed|⚠<br>Skipped|∑<br>Total|⏳<br>Elapsed|🦥<br>Slowest|🐘<br>Heaviest|
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
|_**Sum**_|-|-|1|1|0ms|-|-|
|||||||||
|⚠&nbsp;&nbsp;lib.c|-|-|1|1|0ms|-|-|
"""
    )
