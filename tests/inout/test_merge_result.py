import json
import pathlib
import tempfile
from datetime import datetime, timedelta, timezone
from typing import Any

import pytest
from pydantic import ValidationError

from competitive_verifier.app import MergeResult
from competitive_verifier.models import (
    FileResult,
    ResultStatus,
    VerificationResult,
    VerifyCommandResult,
)

test_merge_result_params: list[
    tuple[dict[str, VerifyCommandResult], dict[str, Any]]
] = [
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
        },
        {
            "total_seconds": 1.25,
            "files": {
                "file1.txt": {
                    "newest": False,
                    "verifications": [
                        {
                            "elapsed": 1.2,
                            "last_execution_time": "2025-09-21T08:09:10.001131+09:00",
                            "status": "success",
                            "verification_name": "v1",
                        },
                    ],
                },
                "file2.txt": {
                    "newest": True,
                    "verifications": [
                        {
                            "elapsed": 1.3,
                            "last_execution_time": "2025-09-21T08:09:11.004253-09:00",
                            "status": "success",
                            "verification_name": "v2",
                        },
                    ],
                },
            },
        },
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
        {
            "total_seconds": 2.69,
            "files": {
                "file1.txt": {
                    "newest": True,
                    "verifications": [
                        {
                            "elapsed": 1.7,
                            "last_execution_time": "2025-09-21T08:09:11.063474Z",
                            "status": "failure",
                            "verification_name": "v3",
                        },
                    ],
                },
                "file2.txt": {
                    "newest": True,
                    "verifications": [
                        {
                            "elapsed": 1.3,
                            "last_execution_time": "2025-09-21T08:09:11.004253-09:00",
                            "status": "success",
                            "verification_name": "v2",
                        },
                    ],
                },
            },
        },
    ),
]


@pytest.mark.parametrize(("files", "expected"), test_merge_result_params)
def test_merge_result(
    files: dict[str, VerifyCommandResult],
    expected: dict[str, Any],
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

    assert MergeResult(result_json=file_list).run()
    out, err = capsys.readouterr()
    assert err == ""
    assert json.loads(out) == expected


def test_merge_result_error():
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
            MergeResult(result_json=[tmpdir / "ok.json", tmpdir / "ng.json"]).run()
