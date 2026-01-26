import logging
import pathlib
import tempfile
from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from competitive_verifier.app import Check
from competitive_verifier.models import (
    FileResult,
    ResultStatus,
    VerificationResult,
    VerifyCommandResult,
)

test_check_params: list[tuple[dict[str, VerifyCommandResult], str, bool]] = [
    (
        {
            "file1.json": VerifyCommandResult(
                total_seconds=1.25,
                files={
                    pathlib.Path("file1.txt"): FileResult(
                        newest=False,
                        verifications=[
                            VerificationResult(
                                verification_name="v1",
                                status=ResultStatus.SUCCESS,
                                last_execution_time=datetime(
                                    2025,
                                    9,
                                    21,
                                    8,
                                    9,
                                    10,
                                    1131,
                                    tzinfo=timezone(timedelta(hours=+9)),
                                ),
                                elapsed=1.2,
                            ),
                        ],
                    ),
                    pathlib.Path("file2.txt"): FileResult(
                        newest=True,
                        verifications=[
                            VerificationResult(
                                verification_name="v2",
                                status=ResultStatus.SKIPPED,
                                last_execution_time=datetime(
                                    2025,
                                    9,
                                    21,
                                    8,
                                    9,
                                    11,
                                    4253,
                                    tzinfo=timezone(timedelta(hours=-9)),
                                ),
                                elapsed=1.3,
                            ),
                        ],
                    ),
                },
            ),
        },
        "success: 1\nfailure: 0\nskipped: 1\n",
        True,
    ),
    (
        {
            "file1.json": VerifyCommandResult(
                total_seconds=1.25,
                files={
                    pathlib.Path("file1.txt"): FileResult(
                        newest=False,
                        verifications=[
                            VerificationResult(
                                verification_name="v1",
                                status=ResultStatus.SUCCESS,
                                last_execution_time=datetime(
                                    2025,
                                    9,
                                    21,
                                    8,
                                    9,
                                    10,
                                    1131,
                                    tzinfo=timezone(timedelta(hours=+9)),
                                ),
                                elapsed=1.2,
                            ),
                        ],
                    ),
                    pathlib.Path("file2.txt"): FileResult(
                        newest=True,
                        verifications=[
                            VerificationResult(
                                verification_name="v2",
                                status=ResultStatus.SUCCESS,
                                last_execution_time=datetime(
                                    2025,
                                    9,
                                    21,
                                    8,
                                    9,
                                    11,
                                    4253,
                                    tzinfo=timezone(timedelta(hours=-9)),
                                ),
                                elapsed=1.3,
                            ),
                        ],
                    ),
                },
            ),
            "file2.json": VerifyCommandResult(
                total_seconds=1.44,
                files={
                    pathlib.Path("file1.txt"): FileResult(
                        newest=True,
                        verifications=[
                            VerificationResult(
                                verification_name="v3",
                                status=ResultStatus.FAILURE,
                                last_execution_time=datetime(
                                    2025,
                                    9,
                                    21,
                                    8,
                                    9,
                                    11,
                                    63474,
                                    tzinfo=timezone.utc,
                                ),
                                elapsed=1.7,
                            ),
                        ],
                    ),
                    pathlib.Path("file2.txt"): FileResult(
                        newest=False,
                        verifications=[
                            VerificationResult(
                                verification_name="v4",
                                status=ResultStatus.FAILURE,
                                last_execution_time=datetime(
                                    2025,
                                    9,
                                    21,
                                    8,
                                    9,
                                    11,
                                    2144,
                                    tzinfo=timezone(timedelta(hours=-1)),
                                ),
                                elapsed=1.9,
                            ),
                        ],
                    ),
                },
            ),
        },
        "success: 1\nfailure: 1\nskipped: 0\n",
        False,
    ),
]


@pytest.mark.parametrize(("files", "expected_out", "expected"), test_check_params)
def test_check(
    files: dict[str, VerifyCommandResult],
    expected_out: str,
    expected: bool,
    tempdir: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    monkeypatch.chdir(tempdir)

    file_list: list[pathlib.Path] = []
    for k, v in files.items():
        p = tempdir / k
        file_list.append(p)
        j = v.model_dump_json()
        p.write_text(j.replace(r"{base}", str(tempdir)))

    assert Check(result_json=file_list).run() == expected
    out, err = capsys.readouterr()
    assert err == ""
    assert out == expected_out


def test_check_error():
    with tempfile.TemporaryDirectory() as tmpdir_s:
        tmpdir = pathlib.Path(tmpdir_s)
        (tmpdir / "ok.json").write_text(r"""{
    "files":{}
}""")
        (tmpdir / "ng.json").write_text(r"""{
    "files":[]
}""")
        with pytest.raises(
            ValidationError, match=r"validation error for VerifyCommandResult"
        ):
            Check(result_json=[tmpdir / "ok.json", tmpdir / "ng.json"]).run()


def test_log(caplog: pytest.LogCaptureFixture):
    caplog.at_level(logging.NOTSET)
    with tempfile.TemporaryDirectory() as tmpdir_s:
        tmpdir = pathlib.Path(tmpdir_s)
        (tmpdir / "success.json").write_text(r"""
{
    "total_seconds": 1.25,
    "files": {
        "file1.txt": {
            "newest": false,
            "verifications": [
                {
                    "elapsed": 1.2,
                    "last_execution_time": "2025-09-21T08:09:10.001131+09:00",
                    "status": "success",
                    "verification_name": "v1"
                }
            ]
        },
        "file2.txt": {
            "newest": true,
            "verifications": [
                {
                    "elapsed": 1.3,
                    "last_execution_time": "2025-09-21T08:09:11.004253-09:00",
                    "status": "success",
                    "verification_name": "v2"
                }
            ]
        }
    }
}""")
        (tmpdir / "failure.json").write_text(r"""
{
    "total_seconds": 1.25,
    "files": {
        "file1.txt": {
            "newest": false,
            "verifications": [
                {
                    "elapsed": 1.2,
                    "last_execution_time": "2025-09-21T08:09:10.001131+09:00",
                    "status": "success",
                    "verification_name": "v3"
                }
            ]
        },
        "file2.txt": {
            "newest": true,
            "verifications": [
                {
                    "elapsed": 1.3,
                    "last_execution_time": "2025-09-21T08:09:11.004253-09:00",
                    "status": "failure",
                    "verification_name": "v4"
                }
            ]
        }
    }
}""")
        assert Check(verbose=True, result_json=[tmpdir / "success.json"]).run()
        assert caplog.record_tuples == []

        assert not Check(
            verbose=True, result_json=[tmpdir / "success.json", tmpdir / "failure.json"]
        ).run()
        assert caplog.record_tuples == [
            ("competitive_verifier.inout.main", logging.ERROR, "Failure test count: 1")
        ]
