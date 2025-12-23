# pyright: reportPrivateUsage=none
import datetime
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from pytest_mock import MockerFixture

from competitive_verifier.models import (
    ConstVerification,
    FileResult,
    ResultStatus,
    VerificationInput,
    VerificationResult,
    VerifyCommandResult,
)
from competitive_verifier.verify.verifier import BaseVerifier, SplitState

SUCCESS = ResultStatus.SUCCESS
FAILURE = ResultStatus.FAILURE


class NotSkippableConstVerification(ConstVerification):
    @property
    def is_lightweight(self) -> bool:
        return False


class MockVerifier(BaseVerifier):
    def __init__(
        self,
        obj: Any = None,
        *,
        prev_result: VerifyCommandResult | None,
        verification_time: datetime.datetime,
        split_state: SplitState | None,
    ) -> None:
        super().__init__(
            verifications=VerificationInput.model_validate(obj),
            verification_time=verification_time,
            prev_result=prev_result,
            split_state=split_state,
            default_tle=10,
            default_mle=256,
            timeout=10,
        )
        self.mock_current_time = datetime.datetime(2006, 1, 2, 15, 4, 5)

    def now(self) -> datetime.datetime:
        dt = self.mock_current_time
        self.mock_current_time = dt + datetime.timedelta(seconds=1)
        return dt

    def get_file_timestamp(self, path: Path) -> datetime.datetime:
        return datetime.datetime(2005, 1, 2, 15, 4, 5)


test_verify_params: list[tuple[MockVerifier, dict[str, Any]]] = [
    (
        MockVerifier(
            {
                "files": {
                    "lib/hoge1.py": {},
                    "test/foo.py": {
                        "dependencies": ["lib/hoge1.py"],
                        "verification": [
                            NotSkippableConstVerification(status=ResultStatus.SUCCESS)
                        ],
                    },
                    "test/skip.py": {
                        "dependencies": ["lib/hoge1.py"],
                        "verification": [
                            ConstVerification(status=ResultStatus.SUCCESS)
                        ],
                    },
                }
            },
            prev_result=None,
            verification_time=datetime.datetime(2007, 1, 2, 15, 4, 5),
            split_state=None,
        ),
        {
            "total_seconds": 8.0,
            "files": {
                "test/foo.py": FileResult(
                    newest=True,
                    verifications=[
                        VerificationResult(
                            status=ResultStatus.SUCCESS,
                            elapsed=2.0,
                            last_execution_time=datetime.datetime(2007, 1, 2, 15, 4, 5),
                        ),
                    ],
                ),
                "test/skip.py": FileResult(
                    newest=True,
                    verifications=[
                        VerificationResult(
                            status=ResultStatus.SUCCESS,
                            elapsed=2.0,
                            last_execution_time=datetime.datetime(2007, 1, 2, 15, 4, 5),
                        ),
                    ],
                ),
            },
        },
    ),
    (
        MockVerifier(
            {
                "files": {
                    "lib/hoge1.py": {},
                    "test/foo.py": {
                        "dependencies": ["lib/hoge1.py"],
                        "verification": [
                            NotSkippableConstVerification(status=ResultStatus.SUCCESS)
                        ],
                    },
                    "test/foo1.py": {
                        "dependencies": ["lib/hoge1.py"],
                        "verification": [
                            NotSkippableConstVerification(status=ResultStatus.SUCCESS)
                        ],
                    },
                    "test/foo2.py": {
                        "dependencies": ["lib/hoge1.py"],
                        "verification": [
                            NotSkippableConstVerification(status=ResultStatus.SUCCESS)
                        ],
                    },
                    "test/foo3.py": {
                        "dependencies": ["lib/hoge1.py"],
                        "verification": [
                            NotSkippableConstVerification(status=ResultStatus.SUCCESS)
                        ],
                    },
                    "test/skip.py": {
                        "dependencies": ["lib/hoge1.py"],
                        "verification": [
                            ConstVerification(status=ResultStatus.SUCCESS)
                        ],
                    },
                }
            },
            prev_result=None,
            verification_time=datetime.datetime(2007, 1, 2, 15, 4, 5),
            split_state=SplitState(size=2, index=0),
        ),
        {
            "total_seconds": 12.0,
            "files": {
                "test/foo.py": FileResult(
                    newest=True,
                    verifications=[
                        VerificationResult(
                            status=ResultStatus.SUCCESS,
                            elapsed=2.0,
                            last_execution_time=datetime.datetime(2007, 1, 2, 15, 4, 5),
                        ),
                    ],
                ),
                "test/foo1.py": FileResult(
                    newest=True,
                    verifications=[
                        VerificationResult(
                            status=ResultStatus.SUCCESS,
                            elapsed=2.0,
                            last_execution_time=datetime.datetime(2007, 1, 2, 15, 4, 5),
                        ),
                    ],
                ),
                "test/skip.py": FileResult(
                    newest=True,
                    verifications=[
                        VerificationResult(
                            status=ResultStatus.SUCCESS,
                            elapsed=2.0,
                            last_execution_time=datetime.datetime(2007, 1, 2, 15, 4, 5),
                        ),
                    ],
                ),
            },
        },
    ),
    (
        MockVerifier(
            {
                "files": {
                    "lib/hoge1.py": {},
                    "test/foo.py": {
                        "dependencies": ["lib/hoge1.py"],
                        "verification": [
                            NotSkippableConstVerification(status=ResultStatus.SUCCESS)
                        ],
                    },
                    "test/foo1.py": {
                        "dependencies": ["lib/hoge1.py"],
                        "verification": [
                            NotSkippableConstVerification(status=ResultStatus.SUCCESS)
                        ],
                    },
                    "test/foo2.py": {
                        "dependencies": ["lib/hoge1.py"],
                        "verification": [
                            NotSkippableConstVerification(status=ResultStatus.SUCCESS)
                        ],
                    },
                    "test/foo3.py": {
                        "dependencies": ["lib/hoge1.py"],
                        "verification": [
                            NotSkippableConstVerification(status=ResultStatus.SUCCESS)
                        ],
                    },
                    "test/skip.py": {
                        "dependencies": ["lib/hoge1.py"],
                        "verification": [
                            ConstVerification(status=ResultStatus.SUCCESS)
                        ],
                    },
                }
            },
            prev_result=None,
            verification_time=datetime.datetime(2007, 1, 2, 15, 4, 5),
            split_state=SplitState(size=2, index=1),
        ),
        {
            "total_seconds": 9.0,
            "files": {
                "test/foo2.py": FileResult(
                    newest=True,
                    verifications=[
                        VerificationResult(
                            status=ResultStatus.SUCCESS,
                            elapsed=2.0,
                            last_execution_time=datetime.datetime(2007, 1, 2, 15, 4, 5),
                        ),
                    ],
                ),
                "test/foo3.py": FileResult(
                    newest=True,
                    verifications=[
                        VerificationResult(
                            status=ResultStatus.SUCCESS,
                            elapsed=2.0,
                            last_execution_time=datetime.datetime(2007, 1, 2, 15, 4, 5),
                        ),
                    ],
                ),
            },
        },
    ),
    (
        MockVerifier(
            {
                "files": {
                    "lib/hoge1.py": {},
                    "test/foo.py": {
                        "dependencies": ["lib/hoge1.py"],
                        "verification": [
                            NotSkippableConstVerification(status=ResultStatus.SUCCESS)
                        ],
                    },
                    "test/foo1.py": {
                        "dependencies": ["lib/hoge1.py"],
                        "verification": [
                            NotSkippableConstVerification(status=ResultStatus.SUCCESS)
                        ],
                    },
                    "test/foo2.py": {
                        "dependencies": ["lib/hoge1.py"],
                        "verification": [
                            NotSkippableConstVerification(status=ResultStatus.SUCCESS)
                        ],
                    },
                    "test/foo3.py": {
                        "dependencies": ["lib/hoge1.py"],
                        "verification": [
                            NotSkippableConstVerification(status=ResultStatus.SUCCESS)
                        ],
                    },
                    "test/skip.py": {
                        "dependencies": ["lib/hoge1.py"],
                        "verification": [
                            ConstVerification(status=ResultStatus.SUCCESS)
                        ],
                    },
                }
            },
            prev_result=VerifyCommandResult.model_validate(
                {
                    "total_seconds": 6.0,
                    "files": {
                        "test/foo.py": FileResult(
                            newest=True,
                            verifications=[
                                VerificationResult(
                                    status=ResultStatus.SUCCESS,
                                    elapsed=1.0,
                                    last_execution_time=datetime.datetime(
                                        2005, 12, 2, 15, 4, 5
                                    ),
                                ),
                            ],
                        ),
                        "test/foo1.py": FileResult(
                            newest=True,
                            verifications=[
                                VerificationResult(
                                    status=ResultStatus.SUCCESS,
                                    elapsed=1.0,
                                    last_execution_time=datetime.datetime(
                                        2005, 12, 2, 15, 4, 5
                                    ),
                                ),
                            ],
                        ),
                        "test/foo2.py": FileResult(
                            newest=True,
                            verifications=[
                                VerificationResult(
                                    status=ResultStatus.SUCCESS,
                                    elapsed=1.0,
                                    last_execution_time=datetime.datetime(
                                        2005, 12, 2, 15, 4, 5
                                    ),
                                ),
                            ],
                        ),
                        "test/foo3.py": FileResult(
                            newest=True,
                            verifications=[
                                VerificationResult(
                                    status=ResultStatus.SUCCESS,
                                    elapsed=1.0,
                                    last_execution_time=datetime.datetime(
                                        2000, 1, 2, 15, 4, 5
                                    ),
                                ),
                            ],
                        ),
                        "test/skip.py": FileResult(
                            newest=False,
                            verifications=[
                                VerificationResult(
                                    status=ResultStatus.SUCCESS,
                                    elapsed=1.0,
                                    last_execution_time=datetime.datetime(
                                        2000, 1, 2, 15, 4, 5
                                    ),
                                ),
                            ],
                        ),
                    },
                }
            ),
            verification_time=datetime.datetime(2007, 1, 2, 15, 4, 5),
            split_state=None,
        ),
        {
            "total_seconds": 8.0,
            "files": {
                "test/foo.py": FileResult(
                    newest=False,
                    verifications=[
                        VerificationResult(
                            status=ResultStatus.SUCCESS,
                            elapsed=1.0,
                            last_execution_time=datetime.datetime(
                                2005, 12, 2, 15, 4, 5
                            ),
                        ),
                    ],
                ),
                "test/foo1.py": FileResult(
                    newest=False,
                    verifications=[
                        VerificationResult(
                            status=ResultStatus.SUCCESS,
                            elapsed=1.0,
                            last_execution_time=datetime.datetime(
                                2005, 12, 2, 15, 4, 5
                            ),
                        ),
                    ],
                ),
                "test/foo2.py": FileResult(
                    newest=False,
                    verifications=[
                        VerificationResult(
                            status=ResultStatus.SUCCESS,
                            elapsed=1.0,
                            last_execution_time=datetime.datetime(
                                2005, 12, 2, 15, 4, 5
                            ),
                        ),
                    ],
                ),
                "test/foo3.py": FileResult(
                    newest=True,
                    verifications=[
                        VerificationResult(
                            status=ResultStatus.SUCCESS,
                            elapsed=2.0,
                            last_execution_time=datetime.datetime(2007, 1, 2, 15, 4, 5),
                        ),
                    ],
                ),
                "test/skip.py": FileResult(
                    newest=True,
                    verifications=[
                        VerificationResult(
                            status=ResultStatus.SUCCESS,
                            elapsed=2.0,
                            last_execution_time=datetime.datetime(2007, 1, 2, 15, 4, 5),
                        ),
                    ],
                ),
            },
        },
    ),
]


@pytest.mark.usefixtures("mock_perf_counter")
@pytest.mark.parametrize(
    ("verifier", "expected"),
    test_verify_params,
    ids=range(len(test_verify_params)),
)
def test_verify(
    verifier: MockVerifier,
    expected: Any,
    mock_exists: Callable[[bool], Any],
):
    mock_exists(True)
    assert verifier.verify() == VerifyCommandResult.model_validate(expected)


test_verify_timeout_params: list[
    tuple[
        MockVerifier,
        list[float],
        dict[str, Any],
    ]
] = [
    (
        MockVerifier(
            {
                "files": {
                    "lib/hoge1.py": {},
                    "test/foo.py": {
                        "dependencies": ["lib/hoge1.py"],
                        "verification": [
                            NotSkippableConstVerification(status=ResultStatus.SUCCESS)
                        ],
                    },
                }
            },
            prev_result=None,
            verification_time=datetime.datetime(2007, 1, 2, 15, 4, 5),
            split_state=None,
        ),
        [0.0, 11.0, 12.0, 13.0, 14.0],
        {
            "total_seconds": 14.0,
            "files": {
                "test/foo.py": FileResult(
                    newest=True,
                    verifications=[
                        VerificationResult(
                            status=ResultStatus.SKIPPED,
                            elapsed=1.0,
                            last_execution_time=datetime.datetime(2007, 1, 2, 15, 4, 5),
                        ),
                    ],
                ),
            },
        },
    ),
    (
        MockVerifier(
            {
                "files": {
                    "lib/hoge1.py": {},
                    "test/foo.py": {
                        "dependencies": ["lib/hoge1.py"],
                        "verification": [
                            NotSkippableConstVerification(status=ResultStatus.SUCCESS)
                        ],
                    },
                }
            },
            prev_result=None,
            verification_time=datetime.datetime(2007, 1, 2, 15, 4, 5),
            split_state=None,
        ),
        [0.0, 5.0, 11.0, 12.0, 13.0],
        {
            "total_seconds": 13.0,
            "files": {
                "test/foo.py": FileResult(
                    newest=True,
                    verifications=[
                        VerificationResult(
                            status=ResultStatus.SKIPPED,
                            elapsed=1.0,
                            last_execution_time=datetime.datetime(2007, 1, 2, 15, 4, 5),
                        ),
                    ],
                ),
            },
        },
    ),
    (
        MockVerifier(
            {
                "files": {
                    "lib/hoge1.py": {},
                    "test/foo.py": {
                        "dependencies": ["lib/hoge1.py"],
                        "verification": [
                            NotSkippableConstVerification(status=ResultStatus.SUCCESS)
                        ],
                    },
                }
            },
            prev_result=None,
            verification_time=datetime.datetime(2007, 1, 2, 15, 4, 5),
            split_state=None,
        ),
        [0.0, 5.0, 6.0, 11.0, 12.0, 13.0],
        {
            "total_seconds": 13.0,
            "files": {
                "test/foo.py": FileResult(
                    newest=True,
                    verifications=[
                        VerificationResult(
                            status=ResultStatus.SKIPPED,
                            elapsed=6.0,
                            last_execution_time=datetime.datetime(2007, 1, 2, 15, 4, 5),
                        ),
                    ],
                ),
            },
        },
    ),
    (
        MockVerifier(
            {
                "files": {
                    "lib/hoge1.py": {},
                    "test/foo1.py": {
                        "dependencies": ["lib/hoge1.py"],
                        "verification": [
                            NotSkippableConstVerification(status=ResultStatus.SUCCESS)
                        ],
                    },
                    "test/foo2.py": {
                        "dependencies": ["lib/hoge1.py"],
                        "verification": [
                            NotSkippableConstVerification(status=ResultStatus.SUCCESS)
                        ],
                    },
                }
            },
            prev_result=None,
            verification_time=datetime.datetime(2007, 1, 2, 15, 4, 5),
            split_state=None,
        ),
        [0.0, 5.0, 6.0, 7.0, 8.0, 11.0, 12.0, 13.0, 14.0],
        {
            "total_seconds": 14.0,
            "files": {
                "test/foo1.py": FileResult(
                    newest=True,
                    verifications=[
                        VerificationResult(
                            status=ResultStatus.SUCCESS,
                            elapsed=2.0,
                            last_execution_time=datetime.datetime(2007, 1, 2, 15, 4, 5),
                        ),
                    ],
                ),
                "test/foo2.py": FileResult(
                    newest=True,
                    verifications=[
                        VerificationResult(
                            status=ResultStatus.SKIPPED,
                            elapsed=1.0,
                            last_execution_time=datetime.datetime(2007, 1, 2, 15, 4, 5),
                        ),
                    ],
                ),
            },
        },
    ),
    (
        MockVerifier(
            {
                "files": {
                    "lib/hoge1.py": {},
                    "test/foo.py": {
                        "dependencies": ["lib/hoge1.py"],
                        "verification": [
                            NotSkippableConstVerification(status=ResultStatus.SUCCESS),
                            NotSkippableConstVerification(status=ResultStatus.SUCCESS),
                        ],
                    },
                }
            },
            prev_result=None,
            verification_time=datetime.datetime(2007, 1, 2, 15, 4, 5),
            split_state=None,
        ),
        [0.0, 5.0, 6.0, 7.0, 8.0, 11.0, 12.0, 13.0],
        {
            "total_seconds": 13.0,
            "files": {
                "test/foo.py": FileResult(
                    newest=True,
                    verifications=[
                        VerificationResult(
                            status=ResultStatus.SUCCESS,
                            elapsed=2.0,
                            last_execution_time=datetime.datetime(2007, 1, 2, 15, 4, 5),
                        ),
                        VerificationResult(
                            status=ResultStatus.SKIPPED,
                            elapsed=1.0,
                            last_execution_time=datetime.datetime(2007, 1, 2, 15, 4, 5),
                        ),
                    ],
                ),
            },
        },
    ),
]


@pytest.mark.parametrize(
    ("verifier", "perf_counter_sequence", "expected"),
    test_verify_timeout_params,
    ids=range(len(test_verify_timeout_params)),
)
def test_verify_timeout(
    mocker: MockerFixture,
    mock_exists: Callable[[bool], Any],
    verifier: MockVerifier,
    perf_counter_sequence: list[float],
    expected: dict[str, Any],
):
    """Test timeout exception scenarios in enumerate_verifications."""
    mock_exists(True)
    mocker.patch("time.perf_counter", side_effect=perf_counter_sequence)
    mocker.patch("competitive_verifier.verify.verifier.run_download", return_value=True)

    result = verifier.verify()
    assert result == VerifyCommandResult.model_validate(expected)
