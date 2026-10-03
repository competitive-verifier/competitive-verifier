import json
import pathlib
from datetime import datetime, timedelta, timezone
from typing import Any

import pytest
from pytest_mock import MockerFixture

from competitive_verifier.models import (
    FileResult,
    NeedVerification,
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
    ("obj", "raw_dict", "output_dict", "output_json"),
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


test_file_result_need_verification_params: list[
    tuple[FileResult, datetime, NeedVerification]
] = [
    (
        FileResult(verifications=[]),
        datetime(2016, 12, 24, 19, 0, 0),
        NeedVerification.NO_RESULT,
    ),
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
        NeedVerification.NO,
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
        NeedVerification.NOT_SUCCESS,
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
        NeedVerification.NOT_SUCCESS,
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
        NeedVerification.MODIFIED,
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
        NeedVerification.MODIFIED,
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
        NeedVerification.NOT_SUCCESS,
    ),
]


@pytest.mark.parametrize(
    ("obj", "dt", "expected"),
    test_file_result_need_verification_params,
)
def test_file_result_need_verification(
    obj: FileResult,
    dt: datetime,
    expected: NeedVerification,
):
    assert obj.need_verification(base_time=dt) is expected
    assert bool(expected) == (expected is not NeedVerification.NO)


def _hashed_result(
    status: ResultStatus, content_hash: str | None, testdata_hash: str | None = None
) -> FileResult:
    return FileResult(
        verifications=[
            VerificationResult(
                elapsed=1.5,
                status=status,
                last_execution_time=datetime(2019, 12, 24, 19, 0, 0),
            ),
        ],
        content_hash=content_hash,
        testdata_hash=testdata_hash,
    )


@pytest.mark.parametrize(
    ("obj", "content_hash", "expected"),
    [
        (FileResult(verifications=[]), "a", NeedVerification.NO_RESULT),
        (
            _hashed_result(ResultStatus.SUCCESS, None),
            "a",
            NeedVerification.NO_CONTENT_HASH,
        ),
        (
            _hashed_result(ResultStatus.SUCCESS, "a"),
            "b",
            NeedVerification.CONTENT_CHANGED,
        ),
        (
            _hashed_result(ResultStatus.SUCCESS, "a"),
            None,
            NeedVerification.CONTENT_CHANGED,
        ),
        (_hashed_result(ResultStatus.FAILURE, "a"), "a", NeedVerification.NOT_SUCCESS),
        (_hashed_result(ResultStatus.SKIPPED, "a"), "a", NeedVerification.NOT_SUCCESS),
        (_hashed_result(ResultStatus.SUCCESS, "a"), "a", NeedVerification.NO),
    ],
)
def test_file_result_need_verification_content_hash(
    obj: FileResult,
    content_hash: str | None,
    expected: NeedVerification,
):
    assert obj.need_verification(content_hash=content_hash) is expected


@pytest.mark.parametrize(
    ("obj", "testdata_hash", "expected"),
    [
        (_hashed_result(ResultStatus.SUCCESS, "a"), None, NeedVerification.NO),
        (_hashed_result(ResultStatus.SUCCESS, "a", "t"), None, NeedVerification.NO),
        (
            _hashed_result(ResultStatus.SUCCESS, "a"),
            "t",
            NeedVerification.NO_TESTDATA_HASH,
        ),
        (
            _hashed_result(ResultStatus.SUCCESS, "a", "t"),
            "u",
            NeedVerification.TESTDATA_CHANGED,
        ),
        (
            _hashed_result(ResultStatus.FAILURE, "a", "t"),
            "t",
            NeedVerification.NOT_SUCCESS,
        ),
        (_hashed_result(ResultStatus.SUCCESS, "a", "t"), "t", NeedVerification.NO),
    ],
)
def test_file_result_need_verification_testdata_hash(
    obj: FileResult,
    testdata_hash: str | None,
    expected: NeedVerification,
):
    assert (
        obj.need_verification(content_hash="a", testdata_hash=testdata_hash) is expected
    )


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
    (
        VerifyCommandResult(
            total_seconds=1,
            files={
                pathlib.Path("failure.c"): FileResult(
                    verifications=[
                        VerificationResult(elapsed=1, status=ResultStatus.SUCCESS),
                        VerificationResult(elapsed=1, status=ResultStatus.FAILURE),
                    ]
                )
            },
        ),
        (False, False),
    ),
    (
        VerifyCommandResult(
            total_seconds=1,
            files={
                pathlib.Path("success.c"): FileResult(
                    verifications=[
                        VerificationResult(elapsed=1, status=ResultStatus.SUCCESS),
                        VerificationResult(elapsed=1, status=ResultStatus.SUCCESS),
                    ]
                ),
            },
        ),
        (True, True),
    ),
    (
        VerifyCommandResult(
            total_seconds=1,
            files={
                pathlib.Path("failure.c"): FileResult(
                    verifications=[
                        VerificationResult(elapsed=1, status=ResultStatus.SUCCESS),
                        VerificationResult(elapsed=1, status=ResultStatus.FAILURE),
                    ]
                ),
                pathlib.Path("success.c"): FileResult(
                    verifications=[
                        VerificationResult(elapsed=1, status=ResultStatus.SUCCESS),
                        VerificationResult(elapsed=1, status=ResultStatus.SUCCESS),
                    ]
                ),
            },
        ),
        (False, False),
    ),
    (
        VerifyCommandResult(
            total_seconds=1,
            files={
                pathlib.Path("skipped.c"): FileResult(
                    verifications=[
                        VerificationResult(elapsed=1, status=ResultStatus.SUCCESS),
                        VerificationResult(elapsed=1, status=ResultStatus.SKIPPED),
                    ]
                ),
                pathlib.Path("success.c"): FileResult(
                    verifications=[
                        VerificationResult(elapsed=1, status=ResultStatus.SUCCESS),
                        VerificationResult(elapsed=1, status=ResultStatus.SUCCESS),
                    ]
                ),
            },
        ),
        (False, True),
    ),
]


@pytest.mark.parametrize(
    ("obj", "expected"),
    test_is_success_params,
)
def test_is_success(
    obj: VerifyCommandResult | FileResult,
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
    ("obj1", "obj2", "expected"),
    test_merge_params,
)
def test_merge(
    obj1: VerifyCommandResult,
    obj2: VerifyCommandResult,
    expected: VerifyCommandResult,
):
    assert obj1.merge(obj2) == expected


def test_parse_file_relative(testtemp: pathlib.Path, mocker: MockerFixture):
    mocker.patch.object(pathlib.Path, "cwd", return_value=testtemp)
    tmp = testtemp / "verify.json"
    with tmp.open("w") as fp:
        json.dump(
            {
                "files": {
                    (testtemp / "libfile.py").as_posix(): {},
                    (testtemp / "libfile2.py").as_posix(): {},
                    "/foo/other/libfile.py": {},
                    (testtemp / "test/test.py").as_posix(): {},
                },
                "total_seconds": 2.5,
            },
            fp,
        )
    assert (
        VerifyCommandResult.parse_file_relative(tmp).model_dump()
        == VerifyCommandResult(
            files={
                pathlib.Path("libfile.py"): FileResult(),
                pathlib.Path("libfile2.py"): FileResult(),
                pathlib.Path("test/test.py"): FileResult(),
            },
            total_seconds=2.5,
        ).model_dump()
    )
