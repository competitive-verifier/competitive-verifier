from datetime import datetime
from pathlib import Path

import pytest

import competitive_verifier.merge_result.main
from competitive_verifier.models import (
    FileResult,
    ResultStatus,
    VerificationResult,
    VerifyCommandResult,
)

test_merge_params: list[tuple[list[VerifyCommandResult], VerifyCommandResult]] = [
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
    "results, expected",
    test_merge_params,
    ids=range(len(test_merge_params)),
)
def test_merge(results: list[VerifyCommandResult], expected: VerifyCommandResult):
    assert competitive_verifier.merge_result.main.merge(results) == expected
