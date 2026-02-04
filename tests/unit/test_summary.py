import logging
import os
import pathlib
from datetime import datetime, timedelta

import pytest
from pytest_mock import MockerFixture

from competitive_verifier import summary
from competitive_verifier.arg import WriteSummaryArguments
from competitive_verifier.models import (
    FileResult,
    JudgeStatus,
    ResultStatus,
    VerificationResult,
    VerifyCommandResult,
)
from competitive_verifier.models import TestcaseResult as CaseResult

test_to_human_str_seconds_params: list[tuple[timedelta, str]] = [
    (timedelta(hours=2, minutes=8, seconds=6, milliseconds=13), "2h 8m"),
    (timedelta(minutes=8, seconds=6, milliseconds=13), "8m 6s"),
    (timedelta(seconds=16, milliseconds=13), "16s"),
    (timedelta(seconds=6, milliseconds=3), "6.0s"),
    (timedelta(seconds=6, milliseconds=13), "6.0s"),
    (timedelta(seconds=6, milliseconds=213), "6.2s"),
    (timedelta(milliseconds=1), "1ms"),
    (timedelta(milliseconds=12), "12ms"),
    (timedelta(milliseconds=123), "123ms"),
]


@pytest.mark.parametrize(
    ("td", "expected"),
    test_to_human_str_seconds_params,
    ids=str,
)
def test_to_human_str_seconds(td: timedelta, expected: str):
    assert summary.to_human_str_seconds(td.total_seconds()) == expected


test_to_human_str_mega_bytes_params: list[tuple[float, str]] = [
    (0.000123456789, "0MB"),
    (0.00123456, "0.00123MB"),
    (0.01234567, "0.0123MB"),
    (0.12345678, "0.123MB"),
    (1.23456789, "1.23MB"),
    (12.3456789, "12.3MB"),
    (123.456789, "123MB"),
    (1234.56789, "1234MB"),
    (12345.6789, "12345MB"),
]


@pytest.mark.parametrize(
    ("megabytes", "expected"),
    test_to_human_str_mega_bytes_params,
)
def test_to_human_str_mega_bytes(megabytes: float, expected: str):
    assert summary.to_human_str_mega_bytes(megabytes) == expected


class MockWriteSummaryArguments(WriteSummaryArguments):
    def run(self) -> bool:
        raise NotImplementedError


def test_no_summary(mocker: MockerFixture):
    mocker.patch.dict(os.environ, {}, clear=True)
    mock_summary = mocker.patch.object(summary, "write_summary")
    MockWriteSummaryArguments(write_summary=False).write_result(
        VerifyCommandResult(files={}, total_seconds=1)
    )
    mock_summary.assert_not_called()


def test_summary_not_exist(mocker: MockerFixture, caplog: pytest.LogCaptureFixture):
    caplog.set_level(logging.NOTSET)
    mocker.patch.dict(os.environ, {}, clear=True)
    mock_summary = mocker.patch.object(summary, "write_summary")

    MockWriteSummaryArguments(write_summary=True).write_result(
        VerifyCommandResult(files={}, total_seconds=1)
    )
    mock_summary.assert_not_called()
    assert caplog.record_tuples == [
        (
            "competitive_verifier.arg",
            logging.WARNING,
            "write_summary=True but not found $GITHUB_STEP_SUMMARY",
        )
    ]


test_summary_params = [
    (
        VerifyCommandResult(
            total_seconds=4.25,
            files={
                pathlib.Path("foo/bar.py"): FileResult(
                    verifications=[
                        VerificationResult(
                            verification_name="ver",
                            heaviest=31.432342,
                            slowest=0.420321,
                            elapsed=1,
                            status=ResultStatus.FAILURE,
                            last_execution_time=datetime.fromtimestamp(1675125600),
                            testcases=[
                                CaseResult(
                                    name="case01",
                                    status=JudgeStatus.TLE,
                                    elapsed=0.2,
                                    memory=30,
                                ),
                                CaseResult(
                                    name="case02",
                                    status=JudgeStatus.WA,
                                    elapsed=0.4,
                                    memory=32,
                                ),
                            ],
                        ),
                        VerificationResult(
                            elapsed=2,
                            status=ResultStatus.FAILURE,
                            last_execution_time=datetime.fromtimestamp(1675125601),
                        ),
                    ]
                ),
                pathlib.Path("foo/baz.py"): FileResult(
                    verifications=[
                        VerificationResult(
                            verification_name="fi",
                            heaviest=31.432342,
                            slowest=0.420321,
                            elapsed=1,
                            status=ResultStatus.SUCCESS,
                            last_execution_time=datetime.fromtimestamp(1675125600),
                            testcases=[
                                CaseResult(
                                    name="case01",
                                    status=JudgeStatus.AC,
                                    elapsed=0.2,
                                    memory=30,
                                ),
                                CaseResult(
                                    name="case02",
                                    status=JudgeStatus.AC,
                                    elapsed=0.4,
                                    memory=32,
                                ),
                            ],
                        ),
                        VerificationResult(
                            elapsed=2,
                            status=ResultStatus.SUCCESS,
                            last_execution_time=datetime.fromtimestamp(1675125601),
                        ),
                    ]
                ),
                pathlib.Path("hoge.py"): FileResult(
                    verifications=[
                        VerificationResult(
                            heaviest=31.432342,
                            slowest=0.420321,
                            elapsed=1,
                            status=ResultStatus.FAILURE,
                            last_execution_time=datetime.fromtimestamp(1675125600),
                            testcases=[
                                CaseResult(
                                    name="case01",
                                    status=JudgeStatus.RE,
                                    elapsed=0.2,
                                    memory=30,
                                ),
                                CaseResult(
                                    name="case02",
                                    status=JudgeStatus.MLE,
                                    elapsed=0.4,
                                    memory=32,
                                ),
                            ],
                        ),
                        VerificationResult(
                            elapsed=2,
                            status=ResultStatus.SUCCESS,
                            last_execution_time=datetime.fromtimestamp(1675125601),
                        ),
                    ]
                ),
                pathlib.Path("piyo.py"): FileResult(
                    verifications=[
                        VerificationResult(
                            elapsed=2,
                            status=ResultStatus.SKIPPED,
                            last_execution_time=datetime.fromtimestamp(1675125601),
                        ),
                    ]
                ),
                pathlib.Path("old.py"): FileResult(
                    newest=False,
                    verifications=[
                        VerificationResult(
                            elapsed=2,
                            status=ResultStatus.SUCCESS,
                            last_execution_time=datetime.fromtimestamp(1675125600),
                        ),
                        VerificationResult(
                            elapsed=2,
                            status=ResultStatus.SUCCESS,
                            last_execution_time=datetime.fromtimestamp(1675125601),
                        ),
                    ],
                ),
            },
        ),
        r"""# ❌ Verification result

- ✔&nbsp;&nbsp;All test case results are `success`
- ❌&nbsp;&nbsp;Test case results containts `failure`
- ⚠&nbsp;&nbsp;Test case results containts `skipped`


## Results
|📝&nbsp;&nbsp;File|✔<br>Passed|❌<br>Failed|⚠<br>Skipped|∑<br>Total|⏳<br>Elapsed|🦥<br>Slowest|🐘<br>Heaviest|
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
|_**Sum**_|3|3|1|7|4.2s|-|-|
|||||||||
|❌&nbsp;&nbsp;foo/bar.py|-|2|-|2|3.0s|420ms|31.4MB|
|✔&nbsp;&nbsp;foo/baz.py|2|-|-|2|3.0s|420ms|31.4MB|
|❌&nbsp;&nbsp;hoge.py|1|1|-|2|3.0s|420ms|31.4MB|
|⚠&nbsp;&nbsp;piyo.py|-|-|1|1|2.0s|-|-|
## Past results
|📝&nbsp;&nbsp;File|✔<br>Passed|❌<br>Failed|⚠<br>Skipped|∑<br>Total|⏳<br>Elapsed|🦥<br>Slowest|🐘<br>Heaviest|
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
|✔&nbsp;&nbsp;old.py|2|-|-|2|4.0s|-|-|
## Failed tests

### foo/bar.py

|env|name|status|Elapsed|Memory|
|:---|:---|:---:|:---:|:---:|
|ver|case01|TLE|200ms|30MB|
|ver|case02|WA|400ms|32MB|
### hoge.py

|env|name|status|Elapsed|Memory|
|:---|:---|:---:|:---:|:---:|
||case01|RE|200ms|30MB|
||case02|MLE|400ms|32MB|
""",
    ),
    (
        VerifyCommandResult(
            total_seconds=11.12,
            files={
                pathlib.Path("hoge.py"): FileResult(
                    verifications=[
                        VerificationResult(
                            elapsed=2,
                            status=ResultStatus.SUCCESS,
                            last_execution_time=datetime.fromtimestamp(1675125600),
                        ),
                    ]
                ),
                pathlib.Path("piyo.py"): FileResult(
                    verifications=[
                        VerificationResult(
                            elapsed=2,
                            status=ResultStatus.SKIPPED,
                            last_execution_time=datetime.fromtimestamp(1675125601),
                        ),
                    ]
                ),
            },
        ),
        r"""# ⚠ Verification result

- ✔&nbsp;&nbsp;All test case results are `success`
- ❌&nbsp;&nbsp;Test case results containts `failure`
- ⚠&nbsp;&nbsp;Test case results containts `skipped`


## Results
|📝&nbsp;&nbsp;File|✔<br>Passed|❌<br>Failed|⚠<br>Skipped|∑<br>Total|⏳<br>Elapsed|🦥<br>Slowest|🐘<br>Heaviest|
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
|_**Sum**_|1|-|1|2|11s|-|-|
|||||||||
|✔&nbsp;&nbsp;hoge.py|1|-|-|1|2.0s|-|-|
|⚠&nbsp;&nbsp;piyo.py|-|-|1|1|2.0s|-|-|
""",
    ),
    (
        VerifyCommandResult(
            total_seconds=11.12,
            files={
                pathlib.Path("hoge.py"): FileResult(
                    verifications=[
                        VerificationResult(
                            elapsed=2,
                            status=ResultStatus.SUCCESS,
                            last_execution_time=datetime.fromtimestamp(1675125600),
                        ),
                    ]
                ),
                pathlib.Path("piyo.py"): FileResult(
                    verifications=[
                        VerificationResult(
                            elapsed=2,
                            status=ResultStatus.SUCCESS,
                            last_execution_time=datetime.fromtimestamp(1675125601),
                        ),
                    ],
                ),
            },
        ),
        r"""# ✔ Verification result

- ✔&nbsp;&nbsp;All test case results are `success`
- ❌&nbsp;&nbsp;Test case results containts `failure`
- ⚠&nbsp;&nbsp;Test case results containts `skipped`


## Results
|📝&nbsp;&nbsp;File|✔<br>Passed|❌<br>Failed|⚠<br>Skipped|∑<br>Total|⏳<br>Elapsed|🦥<br>Slowest|🐘<br>Heaviest|
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
|_**Sum**_|2|-|-|2|11s|-|-|
|||||||||
|✔&nbsp;&nbsp;hoge.py|1|-|-|1|2.0s|-|-|
|✔&nbsp;&nbsp;piyo.py|1|-|-|1|2.0s|-|-|
""",
    ),
    (
        VerifyCommandResult(
            total_seconds=11.12,
            files={
                pathlib.Path("hoge.py"): FileResult(
                    newest=False,
                    verifications=[
                        VerificationResult(
                            elapsed=2,
                            status=ResultStatus.SUCCESS,
                            last_execution_time=datetime.fromtimestamp(1675125600),
                        ),
                    ],
                ),
                pathlib.Path("piyo.py"): FileResult(
                    newest=False,
                    verifications=[
                        VerificationResult(
                            elapsed=2,
                            status=ResultStatus.SUCCESS,
                            last_execution_time=datetime.fromtimestamp(1675125601),
                        ),
                    ],
                ),
            },
        ),
        r"""# ✔ Verification result

- ✔&nbsp;&nbsp;All test case results are `success`
- ❌&nbsp;&nbsp;Test case results containts `failure`
- ⚠&nbsp;&nbsp;Test case results containts `skipped`


## Past results
|📝&nbsp;&nbsp;File|✔<br>Passed|❌<br>Failed|⚠<br>Skipped|∑<br>Total|⏳<br>Elapsed|🦥<br>Slowest|🐘<br>Heaviest|
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
|✔&nbsp;&nbsp;hoge.py|1|-|-|1|2.0s|-|-|
|✔&nbsp;&nbsp;piyo.py|1|-|-|1|2.0s|-|-|
""",
    ),
]


@pytest.mark.parametrize(
    ("verify_command_result", "expected"),
    test_summary_params,
    ids=range(len(test_summary_params)),
)
def test_summary(
    verify_command_result: VerifyCommandResult,
    expected: str,
    mocker: MockerFixture,
    testtemp: pathlib.Path,
):
    tmp = testtemp / "summary.md"
    mocker.patch.dict(
        os.environ,
        {"GITHUB_STEP_SUMMARY": str(tmp)},
        clear=True,
    )
    MockWriteSummaryArguments(write_summary=True).write_result(verify_command_result)

    assert tmp.read_text(encoding="utf-8") == expected.replace("\r\n", "\n")
