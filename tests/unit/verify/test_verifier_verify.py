import datetime
import logging
import os
import pathlib
from typing import Any

import pytest
from pytest_mock import MockerFixture

from competitive_verifier.models import (
    ConstVerification,
    FileResult,
    ProblemVerification,
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
        varifications: Any = None,
        *,
        verification_time: datetime.datetime,
        prev_result: VerifyCommandResult | None = None,
        split_state: SplitState | None = None,
    ) -> None:
        super().__init__(
            verifications=VerificationInput.model_validate(varifications),
            verification_time=verification_time,
            prev_result=prev_result,
            split_state=split_state,
            default_tle=10,
            default_mle=256,
            timeout=10,
        )
        self.mock_current_time = datetime.datetime(2006, 1, 2, 15, 4, 5)

    def get_file_timestamp(self, path: pathlib.Path) -> datetime.datetime:
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
            verification_time=datetime.datetime(2007, 1, 2, 15, 4, 5),
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
)
def test_verify(
    verifier: MockVerifier,
    expected: Any,
    mocker: MockerFixture,
):
    mocker.patch.object(pathlib.Path, "exists", return_value=True)
    assert verifier.verify(download=False) == VerifyCommandResult.model_validate(
        expected
    )


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
            verification_time=datetime.datetime(2007, 1, 2, 15, 4, 5),
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
            verification_time=datetime.datetime(2007, 1, 2, 15, 4, 5),
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
            verification_time=datetime.datetime(2007, 1, 2, 15, 4, 5),
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
            verification_time=datetime.datetime(2007, 1, 2, 15, 4, 5),
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
            verification_time=datetime.datetime(2007, 1, 2, 15, 4, 5),
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


@pytest.mark.usefixtures("mock_perf_counter")
@pytest.mark.parametrize(
    ("verifier", "mock_perf_counter", "expected"),
    test_verify_timeout_params,
    indirect=["mock_perf_counter"],
)
def test_verify_timeout(
    mocker: MockerFixture,
    verifier: MockVerifier,
    expected: dict[str, Any],
):
    """Test timeout exception scenarios in enumerate_verifications."""
    mocker.patch.object(pathlib.Path, "exists", return_value=True)
    download = mocker.patch(
        "competitive_verifier.verify.verifier.run_download", return_value=True
    )

    result = verifier.verify(download=False)
    assert result == VerifyCommandResult.model_validate(expected)
    download.assert_not_called()


@pytest.mark.usefixtures("mock_perf_counter")
def test_verify_download_error(
    mocker: MockerFixture,
    caplog: pytest.LogCaptureFixture,
):
    mocker.patch("competitive_verifier.oj.download", return_value=False)
    verifier = MockVerifier(
        {
            "files": {
                "lib/hoge1.py": {},
                "test/foo.py": {
                    "dependencies": ["lib/hoge1.py"],
                    "verification": [
                        ProblemVerification(
                            name="foo",
                            command="false",
                            problem="https://judge.yosupo.jp/problem/aplusb",
                        ),
                        ProblemVerification(
                            name="bar",
                            command="false",
                            problem="https://judge.yosupo.jp/problem/aplusb",
                        ),
                    ],
                },
            }
        },
        verification_time=datetime.datetime(2007, 1, 2, 15, 4, 5),
    )
    result = verifier.verify(download=True)
    assert result.model_dump(exclude_none=True) == {
        "total_seconds": 4.0,
        "files": {
            pathlib.Path("test/foo.py"): {
                "newest": True,
                "verifications": [
                    {
                        "elapsed": 1.0,
                        "last_execution_time": datetime.datetime(2007, 1, 2, 15, 4, 5),
                        "status": ResultStatus.FAILURE,
                    },
                ],
            }
        },
    }
    assert caplog.record_tuples == [
        (
            "competitive_verifier.verify.verifier",
            logging.ERROR,
            "Failed to download",
        ),
    ]


@pytest.mark.usefixtures("mock_perf_counter")
@pytest.mark.parametrize("is_github_actions", [False, True])
def test_verify_compile_error(
    is_github_actions: bool,
    mocker: MockerFixture,
    caplog: pytest.LogCaptureFixture,
    capsys: pytest.CaptureFixture[str],
):
    mocker.patch.dict(os.environ, {"GITHUB_ACTIONS": str(is_github_actions)})

    mocker.patch.object(
        pathlib.Path, "resolve", return_value=pathlib.Path("/any/dir/test/mock.py")
    )
    mocker.patch(
        "competitive_verifier.models.ProblemVerification.run_compile_command",
        return_value=False,
    )
    verifier = MockVerifier(
        {
            "files": {
                "lib/hoge1.py": {},
                "test/foo.py": {
                    "dependencies": ["lib/hoge1.py"],
                    "verification": [
                        ProblemVerification(
                            name="foo",
                            command="false",
                            problem="https://judge.yosupo.jp/problem/aplusb",
                        ),
                        ProblemVerification(
                            name="bar",
                            command="false",
                            problem="https://judge.yosupo.jp/problem/aplusb",
                        ),
                    ],
                },
            }
        },
        verification_time=datetime.datetime(2007, 1, 2, 15, 4, 5),
    )
    result = verifier.verify(download=False)
    assert result.model_dump(exclude_none=True) == {
        "total_seconds": 6.0,
        "files": {
            pathlib.Path("test/foo.py"): {
                "newest": True,
                "verifications": [
                    {
                        "verification_name": "foo",
                        "elapsed": 1.0,
                        "last_execution_time": datetime.datetime(2007, 1, 2, 15, 4, 5),
                        "status": ResultStatus.FAILURE,
                    },
                    {
                        "verification_name": "bar",
                        "elapsed": 1.0,
                        "last_execution_time": datetime.datetime(2007, 1, 2, 15, 4, 5),
                        "status": ResultStatus.FAILURE,
                    },
                ],
            }
        },
    }
    assert caplog.record_tuples == [
        (
            "competitive_verifier.verify.verifier",
            logging.ERROR,
            f"Failed to compile: {pathlib.Path('test/foo.py')}, ProblemVerification(name='foo', "
            "type='problem', command='false', compile=None, "
            "problem='https://judge.yosupo.jp/problem/aplusb', error=None, "
            "tle=None, mle=None)",
        ),
        (
            "competitive_verifier.verify.verifier",
            logging.ERROR,
            f"Failed to compile: {pathlib.Path('test/foo.py')}, ProblemVerification(name='bar', "
            "type='problem', command='false', compile=None, "
            "problem='https://judge.yosupo.jp/problem/aplusb', error=None, "
            "tle=None, mle=None)",
        ),
    ]

    out, err = capsys.readouterr()

    if is_github_actions:
        assert out == (
            f"::error file={pathlib.Path('/any/dir/test/mock.py')}::Failed to compile test/foo.py\n"
            f"::error file={pathlib.Path('/any/dir/test/mock.py')}::Failed to compile test/foo.py\n"
        )
        assert err == (
            "::group::current_verification_files\n::endgroup::\n"
            "::group::Verify: test/foo.py\n::endgroup::\n"
        )
    else:
        assert out == ""
        assert err == (
            "<------------- \x1b[36m Start group:\x1b[33mcurrent_verification_files\x1b[0m ------------->\n"
            "<------------- \x1b[36mFinish group:\x1b[33mcurrent_verification_files\x1b[0m ------------->\n"
            "<------------- \x1b[36m Start group:\x1b[33mVerify: test/foo.py\x1b[0m ------------->\n"
            "<------------- \x1b[36mFinish group:\x1b[33mVerify: test/foo.py\x1b[0m ------------->\n"
        )


@pytest.mark.usefixtures("mock_perf_counter")
def test_verify_error(
    mocker: MockerFixture,
    caplog: pytest.LogCaptureFixture,
    capsys: pytest.CaptureFixture[str],
):
    class ErrorVerification(ConstVerification):
        @property
        def is_lightweight(self) -> bool:
            return False

        def run(self, *args: Any, **kwargs: Any):  # pyright: ignore[reportIncompatibleMethodOverride]
            raise RuntimeError("ErrorVerification")

    mocker.patch.dict(os.environ, {"GITHUB_ACTIONS": ""})
    verifier = MockVerifier(
        {
            "files": {
                "lib/hoge1.py": {},
                "test/foo.py": {
                    "dependencies": ["lib/hoge1.py"],
                    "verification": [
                        ErrorVerification(
                            name="foo",
                            status=ResultStatus.FAILURE,
                        ),
                    ],
                },
            }
        },
        verification_time=datetime.datetime(2007, 1, 2, 15, 4, 5),
    )
    result = verifier.verify(download=False)
    assert result.model_dump(exclude_none=True) == {
        "total_seconds": 5.0,
        "files": {
            pathlib.Path("test/foo.py"): {
                "newest": True,
                "verifications": [
                    {
                        "verification_name": "foo",
                        "elapsed": 2.0,
                        "last_execution_time": datetime.datetime(2007, 1, 2, 15, 4, 5),
                        "status": ResultStatus.FAILURE,
                    },
                ],
            }
        },
    }
    assert caplog.record_tuples == [
        (
            "competitive_verifier.verify.verifier",
            logging.ERROR,
            f"Failed to verify: {pathlib.Path('test/foo.py')}, "
            "ErrorVerification(name='foo', type='const', status=<ResultStatus.FAILURE: 'failure'>)",
        ),
    ]

    out, err = capsys.readouterr()

    assert out == ""
    assert err == (
        "<------------- \x1b[36m Start group:\x1b[33mcurrent_verification_files\x1b[0m ------------->\n"
        "<------------- \x1b[36mFinish group:\x1b[33mcurrent_verification_files\x1b[0m ------------->\n"
        "<------------- \x1b[36m Start group:\x1b[33mVerify: test/foo.py\x1b[0m ------------->\n"
        "<------------- \x1b[36mFinish group:\x1b[33mVerify: test/foo.py\x1b[0m ------------->\n"
    )


@pytest.mark.usefixtures("mock_perf_counter")
@pytest.mark.parametrize("is_github_actions", [False, True])
def test_verify_failure(
    is_github_actions: bool,
    mocker: MockerFixture,
    caplog: pytest.LogCaptureFixture,
    capsys: pytest.CaptureFixture[str],
):
    mocker.patch.dict(os.environ, {"GITHUB_ACTIONS": str(is_github_actions)})
    mocker.patch.object(
        pathlib.Path, "resolve", return_value=pathlib.Path("/any/dir/test/mock.py")
    )
    verifier = MockVerifier(
        {
            "files": {
                "lib/hoge1.py": {},
                "test/foo.py": {
                    "dependencies": ["lib/hoge1.py"],
                    "verification": [
                        ConstVerification(
                            name="foo",
                            status=ResultStatus.FAILURE,
                        ),
                    ],
                },
            }
        },
        verification_time=datetime.datetime(2007, 1, 2, 15, 4, 5),
    )
    result = verifier.verify(download=False)
    assert result.model_dump(exclude_none=True) == {
        "total_seconds": 4.0,
        "files": {
            pathlib.Path("test/foo.py"): {
                "newest": True,
                "verifications": [
                    {
                        "verification_name": "foo",
                        "elapsed": 2.0,
                        "last_execution_time": datetime.datetime(2007, 1, 2, 15, 4, 5),
                        "status": ResultStatus.FAILURE,
                    },
                ],
            }
        },
    }
    assert caplog.record_tuples == []

    out, err = capsys.readouterr()

    if is_github_actions:
        assert out == ""
        assert err == "::group::current_verification_files\n::endgroup::\n"
    else:
        assert out == ""
        assert err == (
            "<------------- \x1b[36m Start group:\x1b[33mcurrent_verification_files\x1b[0m ------------->\n"
            "<------------- \x1b[36mFinish group:\x1b[33mcurrent_verification_files\x1b[0m ------------->\n"
        )


@pytest.mark.usefixtures("mock_perf_counter")
def test_failure_result():
    class ResultConstVerification(ConstVerification):
        def run(self, *args: Any, **kwargs: Any):  # pyright: ignore[reportIncompatibleMethodOverride]
            return VerificationResult(
                verification_name="mockresult",
                status=self.status,
                elapsed=1.2,
                last_execution_time=datetime.datetime(2007, 1, 2, 10, 4, 5),
            )

    verifier = MockVerifier(
        {
            "files": {
                "lib/hoge1.py": {},
                "test/foo.py": {
                    "dependencies": ["lib/hoge1.py"],
                    "verification": [
                        ResultConstVerification(
                            name="foo",
                            status=ResultStatus.FAILURE,
                        ),
                    ],
                },
            }
        },
        verification_time=datetime.datetime(2007, 1, 2, 15, 4, 5),
    )
    result = verifier.verify(download=False)
    assert result.model_dump(exclude_none=True) == {
        "total_seconds": 3.0,
        "files": {
            pathlib.Path("test/foo.py"): {
                "newest": True,
                "verifications": [
                    {
                        "verification_name": "mockresult",
                        "elapsed": 1.2,
                        "last_execution_time": datetime.datetime(2007, 1, 2, 10, 4, 5),
                        "status": ResultStatus.FAILURE,
                    },
                ],
            }
        },
    }
