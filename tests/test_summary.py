import pathlib
from datetime import datetime, timedelta
from io import StringIO

import pytest

import competitive_verifier.summary as summary
from competitive_verifier.models import FileResult, JudgeStatus, ResultStatus
from competitive_verifier.models import TestcaseResult as CaseResult
from competitive_verifier.models import VerificationResult, VerifyCommandResult

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
    "td, expected",
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
    "megabytes, expected",
    test_to_human_str_mega_bytes_params,
)
def test_to_human_str_mega_bytes(megabytes: float, expected: str):
    assert summary.to_human_str_mega_bytes(megabytes) == expected


def test_summary():
    with StringIO() as fp:
        summary.write_summary(
            fp=fp,
            result=VerifyCommandResult(
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
                },
            ),
        )

        expected = r"""# ❌ Verification result

- ✔&nbsp;&nbsp;All test case results are `success`
- ❌&nbsp;&nbsp;Test case results containts `failure`
- ⚠&nbsp;&nbsp;Test case results containts `skipped`


## Results
|📝&nbsp;&nbsp;File|✔<br>Passed|❌<br>Failed|⚠<br>Skipped|∑<br>Total|⏳<br>Elapsed|🦥<br>Slowest|🐘<br>Heaviest|
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
|_**Sum**_|3|3|-|6|4.2s|-|-|
|||||||||
|❌&nbsp;&nbsp;foo/bar.py|-|2|-|2|3.0s|420ms|31.4MB|
|✔&nbsp;&nbsp;foo/baz.py|2|-|-|2|3.0s|420ms|31.4MB|
|❌&nbsp;&nbsp;hoge.py|1|1|-|2|3.0s|420ms|31.4MB|
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
"""
        assert fp.getvalue() == expected.replace("\r\n", "\n")
