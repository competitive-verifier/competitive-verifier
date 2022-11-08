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
            command_results=[
                VerificationResult(
                    elapsed=1.5,
                    status=ResultStatus.SUCCESS,
                    last_execution_time=datetime(2016, 12, 24, 15, 16, 34),
                )
            ]
        ),
        {
            "command_results": [
                {
                    "status": "success",
                    "elapsed": 1.5,
                    "last_execution_time": "2016-12-24 15:16:34",
                }
            ]
        },
        {
            "command_results": [
                {
                    "status": "success",
                    "elapsed": 1.5,
                    "last_execution_time": datetime(2016, 12, 24, 15, 16, 34),
                }
            ]
        },
        {
            "command_results": [
                {
                    "status": "success",
                    "elapsed": 1.5,
                    "last_execution_time": "2016-12-24T15:16:34",
                }
            ]
        },
    ),
    (
        FileResult(
            command_results=[
                VerificationResult(
                    elapsed=1.5,
                    status=ResultStatus.SUCCESS,
                    last_execution_time=datetime(
                        2016, 12, 24, 15, 16, 34, tzinfo=timezone.utc
                    ),
                )
            ]
        ),
        {
            "command_results": [
                {
                    "status": "Success",
                    "elapsed": 1.5,
                    "last_execution_time": "2016-12-24 15:16:34Z",
                }
            ]
        },
        {
            "command_results": [
                {
                    "status": "success",
                    "elapsed": 1.5,
                    "last_execution_time": datetime(
                        2016, 12, 24, 15, 16, 34, tzinfo=timezone.utc
                    ),
                }
            ]
        },
        {
            "command_results": [
                {
                    "status": "success",
                    "elapsed": 1.5,
                    "last_execution_time": "2016-12-24T15:16:34+00:00",
                }
            ]
        },
    ),
    (
        FileResult(
            command_results=[
                VerificationResult(
                    elapsed=1.5,
                    status=ResultStatus.SUCCESS,
                    last_execution_time=datetime(
                        2016, 12, 24, 15, 16, 34, tzinfo=timezone(timedelta(hours=9))
                    ),
                )
            ]
        ),
        {
            "command_results": [
                {
                    "elapsed": 1.5,
                    "status": "SUCCESS",
                    "last_execution_time": "2016-12-24 15:16:34+09:00",
                }
            ]
        },
        {
            "command_results": [
                {
                    "elapsed": 1.5,
                    "status": "success",
                    "last_execution_time": datetime(
                        2016, 12, 24, 15, 16, 34, tzinfo=timezone(timedelta(hours=9))
                    ),
                }
            ]
        },
        {
            "command_results": [
                {
                    "status": "success",
                    "elapsed": 1.5,
                    "last_execution_time": "2016-12-24T15:16:34+09:00",
                }
            ]
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
    (FileResult(command_results=[]), datetime(2016, 12, 24, 19, 0, 0), False),
    (
        FileResult(
            command_results=[
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
            command_results=[
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
            command_results=[
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
            command_results=[
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
            command_results=[
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
            command_results=[
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
            command_results=[
                VerificationResult(elapsed=1, status=ResultStatus.SUCCESS),
                VerificationResult(elapsed=1, status=ResultStatus.SUCCESS),
            ]
        ),
        True,
    ),
    (
        FileResult(
            command_results=[
                VerificationResult(elapsed=1, status=ResultStatus.SUCCESS),
                VerificationResult(elapsed=1, status=ResultStatus.FAILURE),
            ]
        ),
        False,
    ),
    (
        FileResult(
            command_results=[
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
                command_results=[
                    VerificationResult(elapsed=1, status=ResultStatus.SUCCESS),
                    VerificationResult(elapsed=1, status=ResultStatus.SKIPPED),
                ]
            ),
            pathlib.Path("foo/baz.py"): FileResult(
                command_results=[
                    VerificationResult(elapsed=1, status=ResultStatus.SUCCESS),
                ]
            ),
        },
    )
    assert VerifyCommandResult.parse_raw(obj.json()) == obj
