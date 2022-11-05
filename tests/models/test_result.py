import pathlib
from datetime import datetime, timedelta, timezone
from json import dumps as json_dumps
from typing import Any

import pytest

from competitive_verifier.models.result import VerificationFileResult, ResultStatus

parse_VerificationFileResult_params = [  # type: ignore
    (
        VerificationFileResult(
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
        VerificationFileResult(
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
        VerificationFileResult(
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
    parse_VerificationFileResult_params,
)
def test_parse_VerificationFileResult(
    obj: VerificationFileResult,
    raw_dict: dict[str, Any],
    output_dict: dict[str, Any],
    output_json_dict: dict[str, Any],
):
    assert obj == VerificationFileResult.parse_obj(raw_dict)
    assert obj.dict() == output_dict
    assert obj.json() == json_dumps(output_json_dict)
