import pathlib
from datetime import datetime, timedelta, timezone
from typing import Any

import pytest

from competitive_verifier.models import (
    FileResult,
    ResultStatus,
    VerificationResult,
    VerifyCommandResult,
)

test_parse_FileResult_params: list[
    tuple[FileResult, dict[str, Any], dict[str, Any], str]
] = [
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
        '{"verifications":[{"status":"success","elapsed":1.5,"last_execution_time":"2016-12-24T15:16:34"}],"newest":true}',
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
        '{"verifications":[{"status":"success","elapsed":1.5,"last_execution_time":"2016-12-24T15:16:34Z"}],"newest":false}',
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
        '{"verifications":[{"status":"success","elapsed":1.5,"last_execution_time":"2016-12-24T15:16:34+09:00"}],"newest":true}',
    ),
]


@pytest.mark.parametrize(
    "obj, raw_dict, output_dict, output_json",
    test_parse_FileResult_params,
)
def test_parse_FileResult(
    obj: FileResult,
    raw_dict: dict[str, Any],
    output_dict: dict[str, Any],
    output_json: str,
):
    assert obj == FileResult.model_validate(raw_dict)
    assert obj.model_dump(exclude_none=True) == output_dict
    assert obj.model_dump_json(exclude_none=True) == output_json


test_file_result_need_verification_params: list[tuple[FileResult, datetime, bool]] = [
    (FileResult(verifications=[]), datetime(2016, 12, 24, 19, 0, 0), True),
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
        (True, True),
    ),
    (
        FileResult(
            verifications=[
                VerificationResult(elapsed=1, status=ResultStatus.SUCCESS),
                VerificationResult(elapsed=1, status=ResultStatus.FAILURE),
            ]
        ),
        (False, False),
    ),
    (
        FileResult(
            verifications=[
                VerificationResult(elapsed=1, status=ResultStatus.SUCCESS),
                VerificationResult(elapsed=1, status=ResultStatus.SKIPPED),
            ]
        ),
        (False, True),
    ),
]


@pytest.mark.parametrize(
    "obj, expected",
    test_is_success_params,
)
def test_is_success(
    obj: FileResult,
    expected: tuple[bool, bool],
):
    assert obj.is_success(allow_skip=False) == expected[0]
    assert obj.is_success(allow_skip=True) == expected[1]


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
    assert (
        VerifyCommandResult.model_validate_json(obj.model_dump_json(exclude_none=True))
        == obj
    )


test_merge_params = [
    (
        VerifyCommandResult(
            total_seconds=4.25,
            files={
                pathlib.Path("foo/bar.py"): FileResult(
                    verifications=[
                        VerificationResult(
                            elapsed=1,
                            status=ResultStatus.SUCCESS,
                            last_execution_time=datetime.fromtimestamp(1675125600),
                        ),
                        VerificationResult(
                            elapsed=2,
                            status=ResultStatus.SKIPPED,
                            last_execution_time=datetime.fromtimestamp(1675125601),
                        ),
                    ]
                ),
                pathlib.Path("foo/baz.py"): FileResult(
                    verifications=[
                        VerificationResult(
                            elapsed=3,
                            status=ResultStatus.SUCCESS,
                            last_execution_time=datetime.fromtimestamp(1675125602),
                        ),
                    ]
                ),
            },
        ),
        VerifyCommandResult(
            total_seconds=3,
            files={
                pathlib.Path("foo/bar.py"): FileResult(
                    verifications=[
                        VerificationResult(
                            elapsed=4,
                            status=ResultStatus.SUCCESS,
                            last_execution_time=datetime.fromtimestamp(1675125603),
                        ),
                        VerificationResult(
                            elapsed=5,
                            status=ResultStatus.SKIPPED,
                            last_execution_time=datetime.fromtimestamp(1675125604),
                        ),
                    ]
                ),
                pathlib.Path("foo/baz2.py"): FileResult(
                    verifications=[
                        VerificationResult(
                            elapsed=6,
                            status=ResultStatus.SUCCESS,
                            last_execution_time=datetime.fromtimestamp(1675125605),
                        ),
                    ]
                ),
            },
        ),
        VerifyCommandResult(
            total_seconds=7.25,
            files={
                pathlib.Path("foo/bar.py"): FileResult(
                    verifications=[
                        VerificationResult(
                            elapsed=4,
                            status=ResultStatus.SUCCESS,
                            last_execution_time=datetime.fromtimestamp(1675125603),
                        ),
                        VerificationResult(
                            elapsed=5,
                            status=ResultStatus.SKIPPED,
                            last_execution_time=datetime.fromtimestamp(1675125604),
                        ),
                    ]
                ),
                pathlib.Path("foo/baz.py"): FileResult(
                    verifications=[
                        VerificationResult(
                            elapsed=3,
                            status=ResultStatus.SUCCESS,
                            last_execution_time=datetime.fromtimestamp(1675125602),
                        ),
                    ]
                ),
                pathlib.Path("foo/baz2.py"): FileResult(
                    verifications=[
                        VerificationResult(
                            elapsed=6,
                            status=ResultStatus.SUCCESS,
                            last_execution_time=datetime.fromtimestamp(1675125605),
                        ),
                    ]
                ),
            },
        ),
    ),
    (
        VerifyCommandResult(
            total_seconds=4.25,
            files={
                pathlib.Path("foo/bar.py"): FileResult(
                    verifications=[
                        VerificationResult(
                            elapsed=1,
                            status=ResultStatus.SUCCESS,
                            last_execution_time=datetime.fromtimestamp(1675125600),
                        ),
                        VerificationResult(
                            elapsed=2,
                            status=ResultStatus.SKIPPED,
                            last_execution_time=datetime.fromtimestamp(1675125601),
                        ),
                    ]
                ),
                pathlib.Path("foo/baz.py"): FileResult(
                    verifications=[
                        VerificationResult(
                            elapsed=3,
                            status=ResultStatus.SUCCESS,
                            last_execution_time=datetime.fromtimestamp(1675125602),
                        ),
                    ],
                    newest=True,
                ),
            },
        ),
        VerifyCommandResult(
            total_seconds=3,
            files={
                pathlib.Path("foo/bar.py"): FileResult(
                    verifications=[
                        VerificationResult(
                            elapsed=4,
                            status=ResultStatus.SUCCESS,
                            last_execution_time=datetime.fromtimestamp(1675125603),
                        ),
                        VerificationResult(
                            elapsed=5,
                            status=ResultStatus.SKIPPED,
                            last_execution_time=datetime.fromtimestamp(1675125604),
                        ),
                    ]
                ),
                pathlib.Path("foo/baz.py"): FileResult(
                    verifications=[
                        VerificationResult(
                            elapsed=6,
                            status=ResultStatus.SUCCESS,
                            last_execution_time=datetime.fromtimestamp(1675125605),
                        ),
                    ],
                    newest=False,
                ),
            },
        ),
        VerifyCommandResult(
            total_seconds=7.25,
            files={
                pathlib.Path("foo/bar.py"): FileResult(
                    verifications=[
                        VerificationResult(
                            elapsed=4,
                            status=ResultStatus.SUCCESS,
                            last_execution_time=datetime.fromtimestamp(1675125603),
                        ),
                        VerificationResult(
                            elapsed=5,
                            status=ResultStatus.SKIPPED,
                            last_execution_time=datetime.fromtimestamp(1675125604),
                        ),
                    ]
                ),
                pathlib.Path("foo/baz.py"): FileResult(
                    verifications=[
                        VerificationResult(
                            elapsed=3,
                            status=ResultStatus.SUCCESS,
                            last_execution_time=datetime.fromtimestamp(1675125602),
                        ),
                    ]
                ),
            },
        ),
    ),
    (
        VerifyCommandResult(
            total_seconds=4.25,
            files={
                pathlib.Path("foo/bar.py"): FileResult(
                    verifications=[
                        VerificationResult(
                            elapsed=1,
                            status=ResultStatus.SUCCESS,
                            last_execution_time=datetime.fromtimestamp(1675125600),
                        ),
                        VerificationResult(
                            elapsed=2,
                            status=ResultStatus.SKIPPED,
                            last_execution_time=datetime.fromtimestamp(1675125601),
                        ),
                    ]
                ),
                pathlib.Path("foo/baz.py"): FileResult(
                    verifications=[
                        VerificationResult(
                            elapsed=3,
                            status=ResultStatus.SUCCESS,
                            last_execution_time=datetime.fromtimestamp(1675125602),
                        ),
                    ],
                    newest=False,
                ),
            },
        ),
        VerifyCommandResult(
            total_seconds=3,
            files={
                pathlib.Path("foo/bar.py"): FileResult(
                    verifications=[
                        VerificationResult(
                            elapsed=4,
                            status=ResultStatus.SUCCESS,
                            last_execution_time=datetime.fromtimestamp(1675125603),
                        ),
                        VerificationResult(
                            elapsed=5,
                            status=ResultStatus.SKIPPED,
                            last_execution_time=datetime.fromtimestamp(1675125604),
                        ),
                    ]
                ),
                pathlib.Path("foo/baz.py"): FileResult(
                    verifications=[
                        VerificationResult(
                            elapsed=6,
                            status=ResultStatus.SUCCESS,
                            last_execution_time=datetime.fromtimestamp(1675125605),
                        ),
                    ],
                    newest=True,
                ),
            },
        ),
        VerifyCommandResult(
            total_seconds=7.25,
            files={
                pathlib.Path("foo/bar.py"): FileResult(
                    verifications=[
                        VerificationResult(
                            elapsed=4,
                            status=ResultStatus.SUCCESS,
                            last_execution_time=datetime.fromtimestamp(1675125603),
                        ),
                        VerificationResult(
                            elapsed=5,
                            status=ResultStatus.SKIPPED,
                            last_execution_time=datetime.fromtimestamp(1675125604),
                        ),
                    ]
                ),
                pathlib.Path("foo/baz.py"): FileResult(
                    verifications=[
                        VerificationResult(
                            elapsed=6,
                            status=ResultStatus.SUCCESS,
                            last_execution_time=datetime.fromtimestamp(1675125605),
                        ),
                    ]
                ),
            },
        ),
    ),
    (
        VerifyCommandResult(
            total_seconds=4.25,
            files={
                pathlib.Path("foo/bar.py"): FileResult(
                    verifications=[
                        VerificationResult(
                            elapsed=1,
                            status=ResultStatus.SUCCESS,
                            last_execution_time=datetime.fromtimestamp(1675125600),
                        ),
                        VerificationResult(
                            elapsed=2,
                            status=ResultStatus.SKIPPED,
                            last_execution_time=datetime.fromtimestamp(1675125601),
                        ),
                    ]
                ),
                pathlib.Path("foo/baz.py"): FileResult(
                    verifications=[
                        VerificationResult(
                            elapsed=3,
                            status=ResultStatus.SUCCESS,
                            last_execution_time=datetime.fromtimestamp(1675125602),
                        ),
                    ],
                    newest=True,
                ),
            },
        ),
        VerifyCommandResult(
            total_seconds=3,
            files={
                pathlib.Path("foo/bar.py"): FileResult(
                    verifications=[
                        VerificationResult(
                            elapsed=4,
                            status=ResultStatus.SUCCESS,
                            last_execution_time=datetime.fromtimestamp(1675125603),
                        ),
                        VerificationResult(
                            elapsed=5,
                            status=ResultStatus.SKIPPED,
                            last_execution_time=datetime.fromtimestamp(1675125604),
                        ),
                    ]
                ),
                pathlib.Path("foo/baz.py"): FileResult(
                    verifications=[
                        VerificationResult(
                            elapsed=6,
                            status=ResultStatus.SUCCESS,
                            last_execution_time=datetime.fromtimestamp(1675125605),
                        ),
                    ],
                    newest=True,
                ),
            },
        ),
        VerifyCommandResult(
            total_seconds=7.25,
            files={
                pathlib.Path("foo/bar.py"): FileResult(
                    verifications=[
                        VerificationResult(
                            elapsed=4,
                            status=ResultStatus.SUCCESS,
                            last_execution_time=datetime.fromtimestamp(1675125603),
                        ),
                        VerificationResult(
                            elapsed=5,
                            status=ResultStatus.SKIPPED,
                            last_execution_time=datetime.fromtimestamp(1675125604),
                        ),
                    ]
                ),
                pathlib.Path("foo/baz.py"): FileResult(
                    verifications=[
                        VerificationResult(
                            elapsed=6,
                            status=ResultStatus.SUCCESS,
                            last_execution_time=datetime.fromtimestamp(1675125605),
                        ),
                    ]
                ),
            },
        ),
    ),
]


@pytest.mark.parametrize(
    "obj1, obj2, expected",
    test_merge_params,
)
def test_merge(
    obj1: VerifyCommandResult,
    obj2: VerifyCommandResult,
    expected: VerifyCommandResult,
):
    assert obj1.merge(obj2) == expected
