from datetime import datetime
from pathlib import Path

import pytest

from competitive_verifier import merge
from competitive_verifier.models import (
    FileResult,
    ResultStatus,
    VerificationInput,
    VerificationResult,
    VerifyCommandResult,
)

test_merge_input_params: list[tuple[list[VerificationInput], VerificationInput]] = [
    (
        [
            VerificationInput.model_validate(
                {
                    "files": {
                        "foo/bar.py": {},
                        "foo/baz.py": {
                            "path": "foo/baz.py",
                            "document_attributes": {
                                "title": "foo-baz",
                            },
                            "dependencies": ["foo/bar.py"],
                            "verification": [
                                {
                                    "type": "const",
                                    "status": "success",
                                }
                            ],
                        },
                    },
                }
            ),
        ],
        VerificationInput.model_validate(
            {
                "files": {
                    "foo/bar.py": {},
                    "foo/baz.py": {
                        "path": "foo/baz.py",
                        "document_attributes": {
                            "title": "foo-baz",
                        },
                        "dependencies": ["foo/bar.py"],
                        "verification": [
                            {
                                "type": "const",
                                "status": "success",
                            }
                        ],
                    },
                },
            }
        ),
    ),
    (
        [
            VerificationInput.model_validate(
                {
                    "files": {
                        "foo/bar.py": {},
                        "foo/baz.py": {
                            "path": "foo/baz.py",
                            "document_attributes": {
                                "title": "foo-baz",
                            },
                            "dependencies": ["foo/bar.py"],
                            "verification": [
                                {
                                    "type": "const",
                                    "status": "success",
                                }
                            ],
                        },
                    },
                }
            ),
            VerificationInput.model_validate(
                {
                    "files": {
                        "hoge/bar.py": {},
                        "hoge/baz.py": {
                            "path": "hoge/baz.py",
                            "document_attributes": {
                                "title": "foo-baz",
                            },
                            "dependencies": ["hoge/bar.py"],
                            "verification": [
                                {
                                    "type": "const",
                                    "status": "success",
                                }
                            ],
                        },
                    },
                }
            ),
        ],
        VerificationInput.model_validate(
            {
                "files": {
                    "foo/bar.py": {},
                    "foo/baz.py": {
                        "path": "foo/baz.py",
                        "document_attributes": {
                            "title": "foo-baz",
                        },
                        "dependencies": ["foo/bar.py"],
                        "verification": [
                            {
                                "type": "const",
                                "status": "success",
                            }
                        ],
                    },
                    "hoge/bar.py": {},
                    "hoge/baz.py": {
                        "path": "hoge/baz.py",
                        "document_attributes": {
                            "title": "foo-baz",
                        },
                        "dependencies": ["hoge/bar.py"],
                        "verification": [
                            {
                                "type": "const",
                                "status": "success",
                            }
                        ],
                    },
                },
            }
        ),
    ),
]


@pytest.mark.parametrize(
    ("inputs", "expected"),
    test_merge_input_params,
    ids=range(len(test_merge_input_params)),
)
def test_merge_input(inputs: list[VerificationInput], expected: VerificationInput):
    assert merge.merge(inputs) == expected


test_merge_result_params: list[
    tuple[list[VerifyCommandResult], VerifyCommandResult]
] = [
    (
        [
            VerifyCommandResult(
                total_seconds=2.5,
                files={
                    Path("foo"): FileResult(
                        verifications=[
                            VerificationResult(
                                elapsed=1,
                                status=ResultStatus.SUCCESS,
                                last_execution_time=datetime(2020, 2, 26, 23, 45),
                            )
                        ]
                    )
                },
            ),
        ],
        VerifyCommandResult(
            total_seconds=2.5,
            files={
                Path("foo"): FileResult(
                    verifications=[
                        VerificationResult(
                            elapsed=1,
                            status=ResultStatus.SUCCESS,
                            last_execution_time=datetime(2020, 2, 26, 23, 45),
                        )
                    ]
                )
            },
        ),
    ),
    (
        [
            VerifyCommandResult(
                total_seconds=2.5,
                files={
                    Path("foo"): FileResult(
                        verifications=[
                            VerificationResult(
                                elapsed=1,
                                status=ResultStatus.SUCCESS,
                                last_execution_time=datetime(2020, 2, 26, 23, 45),
                            )
                        ]
                    )
                },
            ),
            VerifyCommandResult(
                total_seconds=4.25,
                files={
                    Path("baz"): FileResult(
                        verifications=[
                            VerificationResult(
                                elapsed=1,
                                status=ResultStatus.SKIPPED,
                                last_execution_time=datetime(2021, 2, 27, 23, 45),
                            )
                        ]
                    )
                },
            ),
            VerifyCommandResult(
                total_seconds=1,
                files={
                    Path("bar"): FileResult(
                        verifications=[
                            VerificationResult(
                                elapsed=1,
                                status=ResultStatus.FAILURE,
                                last_execution_time=datetime(2020, 2, 27, 23, 45),
                            )
                        ]
                    )
                },
            ),
        ],
        VerifyCommandResult(
            total_seconds=7.75,
            files={
                Path("foo"): FileResult(
                    verifications=[
                        VerificationResult(
                            elapsed=1,
                            status=ResultStatus.SUCCESS,
                            last_execution_time=datetime(2020, 2, 26, 23, 45),
                        )
                    ]
                ),
                Path("bar"): FileResult(
                    verifications=[
                        VerificationResult(
                            elapsed=1,
                            status=ResultStatus.FAILURE,
                            last_execution_time=datetime(2020, 2, 27, 23, 45),
                        )
                    ]
                ),
                Path("baz"): FileResult(
                    verifications=[
                        VerificationResult(
                            elapsed=1,
                            status=ResultStatus.SKIPPED,
                            last_execution_time=datetime(2021, 2, 27, 23, 45),
                        )
                    ]
                ),
            },
        ),
    ),
]


@pytest.mark.parametrize(
    ("results", "expected"),
    test_merge_result_params,
    ids=range(len(test_merge_result_params)),
)
def test_merge_result(
    results: list[VerifyCommandResult], expected: VerifyCommandResult
):
    assert merge.merge(results) == expected
