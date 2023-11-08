# pyright: reportPrivateUsage=none
import datetime
from pathlib import Path
from typing import Any, Callable, Optional

import pytest

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
    def is_skippable(self) -> bool:
        return False


class MockVerifier(BaseVerifier):
    def __init__(
        self,
        obj: Any = None,
        *,
        prev_result: Optional[VerifyCommandResult],
        verification_time: datetime.datetime,
        split_state: Optional[SplitState],
    ) -> None:
        super().__init__(
            input=VerificationInput.model_validate(obj),
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
            "total_seconds": 6.0,
            "files": {
                "test/foo.py": FileResult(
                    newest=True,
                    verifications=[
                        VerificationResult(
                            status=ResultStatus.SUCCESS,
                            elapsed=1.0,
                            last_execution_time=datetime.datetime(2007, 1, 2, 15, 4, 5),
                        ),
                    ],
                ),
                "test/skip.py": FileResult(
                    newest=True,
                    verifications=[
                        VerificationResult(
                            status=ResultStatus.SUCCESS,
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
            "total_seconds": 9.0,
            "files": {
                "test/foo.py": FileResult(
                    newest=True,
                    verifications=[
                        VerificationResult(
                            status=ResultStatus.SUCCESS,
                            elapsed=1.0,
                            last_execution_time=datetime.datetime(2007, 1, 2, 15, 4, 5),
                        ),
                    ],
                ),
                "test/foo1.py": FileResult(
                    newest=True,
                    verifications=[
                        VerificationResult(
                            status=ResultStatus.SUCCESS,
                            elapsed=1.0,
                            last_execution_time=datetime.datetime(2007, 1, 2, 15, 4, 5),
                        ),
                    ],
                ),
                "test/skip.py": FileResult(
                    newest=True,
                    verifications=[
                        VerificationResult(
                            status=ResultStatus.SUCCESS,
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
            "total_seconds": 7.0,
            "files": {
                "test/foo2.py": FileResult(
                    newest=True,
                    verifications=[
                        VerificationResult(
                            status=ResultStatus.SUCCESS,
                            elapsed=1.0,
                            last_execution_time=datetime.datetime(2007, 1, 2, 15, 4, 5),
                        ),
                    ],
                ),
                "test/foo3.py": FileResult(
                    newest=True,
                    verifications=[
                        VerificationResult(
                            status=ResultStatus.SUCCESS,
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
                    "total_seconds": 7.0,
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
            "total_seconds": 6.0,
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
                            elapsed=1.0,
                            last_execution_time=datetime.datetime(2007, 1, 2, 15, 4, 5),
                        ),
                    ],
                ),
                "test/skip.py": FileResult(
                    newest=True,
                    verifications=[
                        VerificationResult(
                            status=ResultStatus.SUCCESS,
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
    "verifier, expected",
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
