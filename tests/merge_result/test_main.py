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
                files={
                    Path("foo"): FileResult(
                        command_results=[
                            VerificationResult(
                                status=ResultStatus.SUCCESS,
                                last_execution_time=datetime(2020, 2, 26, 23, 45),
                            )
                        ]
                    )
                }
            ),
        ],
        VerifyCommandResult(
            files={
                Path("foo"): FileResult(
                    command_results=[
                        VerificationResult(
                            status=ResultStatus.SUCCESS,
                            last_execution_time=datetime(2020, 2, 26, 23, 45),
                        )
                    ]
                )
            }
        ),
    ),
    (
        [
            VerifyCommandResult(
                files={
                    Path("foo"): FileResult(
                        command_results=[
                            VerificationResult(
                                status=ResultStatus.SUCCESS,
                                last_execution_time=datetime(2020, 2, 26, 23, 45),
                            )
                        ]
                    )
                }
            ),
            VerifyCommandResult(
                files={
                    Path("baz"): FileResult(
                        command_results=[
                            VerificationResult(
                                status=ResultStatus.SKIPPED,
                                last_execution_time=datetime(2021, 2, 27, 23, 45),
                            )
                        ]
                    )
                }
            ),
            VerifyCommandResult(
                files={
                    Path("bar"): FileResult(
                        command_results=[
                            VerificationResult(
                                status=ResultStatus.FAILURE,
                                last_execution_time=datetime(2020, 2, 27, 23, 45),
                            )
                        ]
                    )
                }
            ),
        ],
        VerifyCommandResult(
            files={
                Path("foo"): FileResult(
                    command_results=[
                        VerificationResult(
                            status=ResultStatus.SUCCESS,
                            last_execution_time=datetime(2020, 2, 26, 23, 45),
                        )
                    ]
                ),
                Path("bar"): FileResult(
                    command_results=[
                        VerificationResult(
                            status=ResultStatus.FAILURE,
                            last_execution_time=datetime(2020, 2, 27, 23, 45),
                        )
                    ]
                ),
                Path("baz"): FileResult(
                    command_results=[
                        VerificationResult(
                            status=ResultStatus.SKIPPED,
                            last_execution_time=datetime(2021, 2, 27, 23, 45),
                        )
                    ]
                ),
            }
        ),
    ),
]


@pytest.mark.parametrize("results, expected", test_merge_params)
def test_merge(results: list[VerifyCommandResult], expected: VerifyCommandResult):
    assert competitive_verifier.merge_result.main.merge(results) == expected
