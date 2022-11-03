import pathlib
from datetime import datetime, timedelta, timezone
from json import dumps as json_dumps
from typing import Any

import pytest

from competitive_verifier.models.result import FileVerificationResult, ResultStatus

parse_FileVerificationResult_params = [  # type: ignore
    (
        FileVerificationResult(
            path=pathlib.Path("foo/bar"),
            command_result=ResultStatus.SUCCESS,
            last_success_time=datetime(2016, 12, 24, 15, 16, 34),
        ),
        {
            "path": "foo/bar",
            "command_result": "SUCCESS",
            "last_success_time": "2016-12-24 15:16:34",
        },
        {
            "path": pathlib.Path("foo/bar"),
            "command_result": "SUCCESS",
            "last_success_time": datetime(2016, 12, 24, 15, 16, 34),
        },
        {
            "path": str(pathlib.Path("foo/bar")),
            "command_result": "SUCCESS",
            "last_success_time": "2016-12-24T15:16:34",
        },
    ),
    (
        FileVerificationResult(
            path=pathlib.Path("foo/bar"),
            command_result=ResultStatus.SUCCESS,
            last_success_time=datetime(2016, 12, 24, 15, 16, 34, tzinfo=timezone.utc),
        ),
        {
            "path": "foo/bar",
            "command_result": "SUCCESS",
            "last_success_time": "2016-12-24 15:16:34Z",
        },
        {
            "path": pathlib.Path("foo/bar"),
            "command_result": "SUCCESS",
            "last_success_time": datetime(
                2016, 12, 24, 15, 16, 34, tzinfo=timezone.utc
            ),
        },
        {
            "path": str(pathlib.Path("foo/bar")),
            "command_result": "SUCCESS",
            "last_success_time": "2016-12-24T15:16:34+00:00",
        },
    ),
    (
        FileVerificationResult(
            path=pathlib.Path("foo/bar"),
            command_result=ResultStatus.SUCCESS,
            last_success_time=datetime(
                2016, 12, 24, 15, 16, 34, tzinfo=timezone(timedelta(hours=9))
            ),
        ),
        {
            "path": "foo/bar",
            "command_result": "SUCCESS",
            "last_success_time": "2016-12-24 15:16:34+09:00",
        },
        {
            "path": pathlib.Path("foo/bar"),
            "command_result": "SUCCESS",
            "last_success_time": datetime(
                2016, 12, 24, 15, 16, 34, tzinfo=timezone(timedelta(hours=9))
            ),
        },
        {
            "path": str(pathlib.Path("foo/bar")),
            "command_result": "SUCCESS",
            "last_success_time": "2016-12-24T15:16:34+09:00",
        },
    ),
]


@pytest.mark.parametrize(
    "obj, raw_dict, output_dict, output_json_dict",
    parse_FileVerificationResult_params,
)
def test_parse_FileVerificationResult(
    obj: FileVerificationResult,
    raw_dict: dict[str, Any],
    output_dict: dict[str, Any],
    output_json_dict: dict[str, Any],
):
    assert obj == FileVerificationResult.parse_obj(raw_dict)
    assert obj.dict() == output_dict
    assert obj.json() == json_dumps(output_json_dict)
