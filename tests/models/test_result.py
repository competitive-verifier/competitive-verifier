import pathlib
from datetime import datetime, timedelta, timezone
from json import dumps as json_dumps
from typing import Any

import pytest

from competitive_verifier.models import (
    FileResult,
    ResultStatus,
    VerificationResult,
    VerifyCommandResult,
)

test_parse_FileResult_params = [  # type: ignore
    (
        FileResult(
            verifications=[
                VerificationResult(
                    elapsed=1.5,
                    status=ResultStatus.SUCCESS,
                    last_execution_time=datetime(2016, 12, 24, 15, 16, 34),
                )
            ],
        ),
        {
            "verifications": [
                {
                    "status": "success",
                    "elapsed": 1.5,
                    "last_execution_time": "2016-12-24 15:16:34",
                }
            ],
            "newest": True,
        },
        {
            "verifications": [
                {
                    "status": "success",
                    "elapsed": 1.5,
                    "last_execution_time": datetime(2016, 12, 24, 15, 16, 34),
                }
            ],
            "newest": True,
        },
        {
            "verifications": [
                {
                    "status": "success",
                    "elapsed": 1.5,
                    "last_execution_time": "2016-12-24T15:16:34",
                }
            ],
            "newest": True,
        },
    ),
    (
        FileResult(
            newest=False,
            verifications=[
                VerificationResult(
                    elapsed=1.5,
                    status=ResultStatus.SUCCESS,
                    last_execution_time=datetime(
                        2016, 12, 24, 15, 16, 34, tzinfo=timezone.utc
                    ),
                )
            ],
        ),
        {
            "newest": False,
            "verifications": [
                {
                    "status": "Success",
                    "elapsed": 1.5,
                    "last_execution_time": "2016-12-24 15:16:34Z",
                }
            ],
        },
        {
            "verifications": [
                {
                    "status": "success",
                    "elapsed": 1.5,
                    "last_execution_time": datetime(
                        2016, 12, 24, 15, 16, 34, tzinfo=timezone.utc
                    ),
                }
            ],
            "newest": False,
        },
        {
            "verifications": [
                {
                    "status": "success",
                    "elapsed": 1.5,
                    "last_execution_time": "2016-12-24T15:16:34+00:00",
                }
            ],
            "newest": False,
        },
    ),
    (
        FileResult(
            newest=True,
            verifications=[
                VerificationResult(
                    elapsed=1.5,
                    status=ResultStatus.SUCCESS,
                    last_execution_time=datetime(
                        2016, 12, 24, 15, 16, 34, tzinfo=timezone(timedelta(hours=9))
                    ),
                )
            ],
        ),
        {
            "verifications": [
                {
                    "elapsed": 1.5,
                    "status": "SUCCESS",
                    "last_execution_time": "2016-12-24 15:16:34+09:00",
                }
            ]
        },
        {
            "verifications": [
                {
                    "elapsed": 1.5,
                    "status": "success",
                    "last_execution_time": datetime(
                        2016, 12, 24, 15, 16, 34, tzinfo=timezone(timedelta(hours=9))
                    ),
                }
            ],
            "newest": True,
        },
        {
            "verifications": [
                {
                    "status": "success",
                    "elapsed": 1.5,
                    "last_execution_time": "2016-12-24T15:16:34+09:00",
                }
            ],
            "newest": True,
        },
    ),
]


@pytest.mark.parametrize(
    "obj, raw_dict, output_dict, output_json_dict",
    test_parse_FileResult_params,
)
def test_parse_FileResult(
    obj: FileResult,
    raw_dict: dict[str, Any],
    output_dict: dict[str, Any],
    output_json_dict: dict[str, Any],
):
    assert obj == FileResult.parse_obj(raw_dict)
    assert obj.dict() == output_dict
    assert obj.json() == json_dumps(output_json_dict)


test_file_result_need_verification_params = [  # type: ignore
    (FileResult(verifications=[]), datetime(2016, 12, 24, 19, 0, 0), False),
    (
        FileResult(
            verifications=[
                VerificationResult(
                    elapsed=1.5,
                    status=ResultStatus.SUCCESS,
                    last_execution_time=datetime(2019, 12, 24, 19, 0, 0),
                )
            ]
        ),
        datetime(2016, 12, 24, 19, 0, 0),
        False,
    ),
    (
        FileResult(
            verifications=[
                VerificationResult(
                    elapsed=1.5,
                    status=ResultStatus.FAILURE,
                    last_execution_time=datetime(2019, 12, 24, 19, 0, 0),
                )
            ]
        ),
        datetime(2016, 12, 24, 19, 0, 0),
        True,
    ),
    (
        FileResult(
            verifications=[
                VerificationResult(
                    elapsed=1.5,
                    status=ResultStatus.SKIPPED,
                    last_execution_time=datetime(2019, 12, 24, 19, 0, 0),
                )
            ]
        ),
        datetime(2016, 12, 24, 19, 0, 0),
        True,
    ),
    (
        FileResult(
            verifications=[
                VerificationResult(
                    elapsed=1.5,
                    status=ResultStatus.SUCCESS,
                    last_execution_time=datetime(2015, 12, 24, 19, 0, 0),
                )
            ]
        ),
        datetime(2016, 12, 24, 19, 0, 0),
        True,
    ),
    (
        FileResult(
            verifications=[
                VerificationResult(
                    elapsed=1.5,
                    status=ResultStatus.SUCCESS,
                    last_execution_time=datetime(2018, 12, 24, 19, 0, 0),
                ),
                VerificationResult(
                    elapsed=1.5,
                    status=ResultStatus.SUCCESS,
                    last_execution_time=datetime(2018, 12, 24, 19, 0, 0),
                ),
                VerificationResult(
                    elapsed=1.5,
                    status=ResultStatus.SUCCESS,
                    last_execution_time=datetime(2015, 12, 24, 19, 0, 0),
                ),
            ]
        ),
        datetime(2016, 12, 24, 19, 0, 0),
        True,
    ),
    (
        FileResult(
            verifications=[
                VerificationResult(
                    elapsed=1.5,
                    status=ResultStatus.SUCCESS,
                    last_execution_time=datetime(2018, 12, 24, 19, 0, 0),
                ),
                VerificationResult(
                    elapsed=1.5,
                    status=ResultStatus.SUCCESS,
                    last_execution_time=datetime(2018, 12, 24, 19, 0, 0),
                ),
                VerificationResult(
                    elapsed=1.5,
                    status=ResultStatus.FAILURE,
                    last_execution_time=datetime(2018, 12, 24, 19, 0, 0),
                ),
            ]
        ),
        datetime(2016, 12, 24, 19, 0, 0),
        True,
    ),
]


@pytest.mark.parametrize(
    "obj, dt, expected",
    test_file_result_need_verification_params,
)
def test_file_result_need_verification(
    obj: FileResult,
    dt: datetime,
    expected: bool,
):
    assert obj.need_verification(dt) == expected


test_is_success_params = [
    (
        FileResult(
            verifications=[
                VerificationResult(elapsed=1, status=ResultStatus.SUCCESS),
                VerificationResult(elapsed=1, status=ResultStatus.SUCCESS),
            ]
        ),
        True,
    ),
    (
        FileResult(
            verifications=[
                VerificationResult(elapsed=1, status=ResultStatus.SUCCESS),
                VerificationResult(elapsed=1, status=ResultStatus.FAILURE),
            ]
        ),
        False,
    ),
    (
        FileResult(
            verifications=[
                VerificationResult(elapsed=1, status=ResultStatus.SUCCESS),
                VerificationResult(elapsed=1, status=ResultStatus.SKIPPED),
            ]
        ),
        False,
    ),
]


@pytest.mark.parametrize(
    "obj, expected",
    test_is_success_params,
)
def test_is_success(
    obj: FileResult,
    expected: bool,
):
    assert obj.is_success() == expected


def test_verify_command_result_json():
    obj = VerifyCommandResult(
        total_seconds=3.75,
        files={
            pathlib.Path("foo/bar.py"): FileResult(
                verifications=[
                    VerificationResult(elapsed=1, status=ResultStatus.SUCCESS),
                    VerificationResult(elapsed=1, status=ResultStatus.SKIPPED),
                ]
            ),
            pathlib.Path("foo/baz.py"): FileResult(
                verifications=[
                    VerificationResult(elapsed=1, status=ResultStatus.SUCCESS),
                ]
            ),
        },
    )
    assert VerifyCommandResult.parse_raw(obj.json()) == obj
