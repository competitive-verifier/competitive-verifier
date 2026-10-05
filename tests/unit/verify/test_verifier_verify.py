import datetime
import logging
import os
import pathlib
from typing import Any, NamedTuple

import pytest
from pytest_mock import MockerFixture, MockType

from competitive_verifier.log import GitHubMessageParams
from competitive_verifier.models import (
    ConstVerification,
    FileResult,
    ProblemVerification,
    ResultStatus,
    VerificationInput,
    VerificationResult,
    VerifyCommandResult,
)
from competitive_verifier.oj.problem import LibraryCheckerProblem
from competitive_verifier.verify.verifier import (
    BaseVerifier,
    ChangeDetection,
    SplitState,
)
from tests import LogComparer

SUCCESS = ResultStatus.SUCCESS
FAILURE = ResultStatus.FAILURE


@pytest.fixture
def mock_update_cloned_repository(mocker: MockerFixture):
    mocker.patch(
        "competitive_verifier.oj.problem.LibraryCheckerProblem.update_cloned_repository"
    )


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
        file_hashes: dict[str, str] | None = None,
        change_detection: ChangeDetection = "timestamp",
    ) -> None:
        super().__init__(
            verifications=VerificationInput.model_validate(varifications),
            verification_time=verification_time,
            prev_result=prev_result,
            split_state=split_state,
            change_detection=change_detection,
            default_tle=10,
            default_mle=256,
            timeout=10,
        )
        self.file_hashes = file_hashes

    def get_file_timestamp(self, path: pathlib.Path) -> datetime.datetime:
        return datetime.datetime(2005, 1, 2, 15, 4, 5)

    def file_content_hash(self, path: pathlib.Path) -> str | None:
        if self.file_hashes is None:
            return None
        return self.file_hashes.get(path.as_posix())


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
                            content_hash="hash:test/foo.py",
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
                            content_hash="hash:test/foo1.py",
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
                            content_hash="hash:test/foo2.py",
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
                            content_hash="outdated-hash",
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
                            content_hash="hash:test/skip.py",
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
            file_hashes={
                "test/foo.py": "hash:test/foo.py",
                "test/foo1.py": "hash:test/foo1.py",
                "test/foo2.py": "hash:test/foo2.py",
                "test/foo3.py": "hash:test/foo3.py",
                "test/skip.py": "hash:test/skip.py",
            },
        ),
        {
            "total_seconds": 8.0,
            "files": {
                "test/foo.py": FileResult(
                    newest=False,
                    content_hash="hash:test/foo.py",
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
                    content_hash="hash:test/foo1.py",
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
                    content_hash="hash:test/foo2.py",
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
                    content_hash="hash:test/foo3.py",
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
                    content_hash="hash:test/skip.py",
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


@pytest.mark.usefixtures("mock_perf_counter", "mock_update_cloned_repository")
def test_verify_download_error(
    mocker: MockerFixture,
    caplog: pytest.LogCaptureFixture,
):
    mocker.patch("competitive_verifier.oj.download", return_value=False)
    verification = [
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
    ]
    verifier = MockVerifier(
        {
            "files": {
                "lib/hoge1.py": {},
                "test/foo.py": {
                    "dependencies": ["lib/hoge1.py"],
                    "verification": verification,
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
    assert caplog.records == [
        LogComparer(
            f"Failed to download: {verification}",
            logging.ERROR,
            github=GitHubMessageParams(),
        ),
    ]


@pytest.mark.usefixtures("mock_perf_counter", "mock_update_cloned_repository")
def test_verify_not_downloaded(
    mocker: MockerFixture,
    caplog: pytest.LogCaptureFixture,
):
    mocker.patch(
        "competitive_verifier.models.ProblemVerification.is_testdata_cached",
        return_value=False,
    )
    verification = [
        ProblemVerification(
            name="foo",
            command="false",
            problem="https://judge.yosupo.jp/problem/aplusb",
        ),
    ]
    verifier = MockVerifier(
        {
            "files": {
                "lib/hoge1.py": {},
                "test/foo.py": {
                    "dependencies": ["lib/hoge1.py"],
                    "verification": verification,
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
                        "elapsed": 1.0,
                        "last_execution_time": datetime.datetime(2007, 1, 2, 15, 4, 5),
                        "status": ResultStatus.FAILURE,
                    },
                ],
            }
        },
    }
    assert caplog.records == [
        LogComparer(
            f"Failed to download: {verification}",
            logging.ERROR,
            github=GitHubMessageParams(),
        ),
    ]


@pytest.mark.usefixtures("mock_perf_counter", "mock_update_cloned_repository")
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
    mocker.patch(
        "competitive_verifier.models.ProblemVerification.is_testdata_cached",
        return_value=True,
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
    assert caplog.records == [
        LogComparer(
            f"Failed to compile: {pathlib.Path('test/foo.py')}, "
            'verification={"name":"foo","command":"false","problem":"https://judge.yosupo.jp/problem/aplusb"}',
            logging.ERROR,
            github=GitHubMessageParams(file=pathlib.Path("test/foo.py")),
        ),
        LogComparer(
            f"Failed to compile: {pathlib.Path('test/foo.py')}, verification="
            '{"name":"bar","command":"false","problem":"https://judge.yosupo.jp/problem/aplusb"}',
            logging.ERROR,
            github=GitHubMessageParams(file=pathlib.Path("test/foo.py")),
        ),
    ]

    out, err = capsys.readouterr()

    assert out == ""
    if is_github_actions:
        assert err == (
            "::group::current_verification_files\n::endgroup::\n"
            "::group::Verify: test/foo.py\n::endgroup::\n"
        )
    else:
        assert err == (
            "<------------- \x1b[36m Start group:\x1b[33mcurrent_verification_files\x1b[0m ------------->\n"
            "<------------- \x1b[36mFinish group:\x1b[33mcurrent_verification_files\x1b[0m ------------->\n"
            "<------------- \x1b[36m Start group:\x1b[33mVerify: test/foo.py\x1b[0m ------------->\n"
            "<------------- \x1b[36mFinish group:\x1b[33mVerify: test/foo.py\x1b[0m ------------->\n"
        )


@pytest.mark.usefixtures("mock_perf_counter", "mock_update_cloned_repository")
def test_verify_error(
    caplog: pytest.LogCaptureFixture,
    capsys: pytest.CaptureFixture[str],
):
    class ErrorVerification(ConstVerification):
        @property
        def is_lightweight(self) -> bool:
            return False

        def run(self, *args: Any, **kwargs: Any):  # pyright: ignore[reportIncompatibleMethodOverride]
            raise RuntimeError("ErrorVerification")

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
    assert caplog.records == [
        LogComparer(
            f"Failed to verify: {pathlib.Path('test/foo.py')}, "
            "ErrorVerification(name='foo', type='const', status=<ResultStatus.FAILURE: 'failure'>)",
            logging.ERROR,
            github=GitHubMessageParams(),
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
    assert not caplog.records

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


class MockSync(NamedTuple):
    update: MockType
    run_download: MockType
    synced_before_hash: list[int]


@pytest.fixture
def mock_sync(mocker: MockerFixture) -> MockSync:
    mocker.patch.object(pathlib.Path, "exists", return_value=True)
    update = mocker.patch.object(LibraryCheckerProblem, "update_cloned_repository")
    run_download = mocker.patch(
        "competitive_verifier.verify.verifier.run_download", return_value=True
    )
    synced_before_hash: list[int] = []

    def file_testdata_hash(path: pathlib.Path) -> str:
        synced_before_hash.append(update.call_count)
        return "testdata-foo"

    mocker.patch.object(
        MockVerifier, "file_testdata_hash", side_effect=file_testdata_hash
    )
    return MockSync(
        update=update,
        run_download=run_download,
        synced_before_hash=synced_before_hash,
    )


@pytest.mark.usefixtures("mock_perf_counter", "mock_update_cloned_repository")
@pytest.mark.parametrize(
    ("download", "change_detection"),
    [
        (True, "hash"),
        (False, "hash"),
        (True, "timestamp"),
        (False, "timestamp"),
    ],
)
def test_verify_syncs_testdata_before_skip_selection(
    mock_sync: MockSync,
    download: bool,
    change_detection: ChangeDetection,
):
    update = mock_sync.update

    verifier = MockVerifier(
        {
            "files": {
                "test/foo.py": {
                    "verification": ProblemVerification(
                        command="false",
                        problem="https://judge.yosupo.jp/problem/aplusb",
                    ),
                },
            }
        },
        verification_time=datetime.datetime(2007, 1, 2, 15, 4, 5),
        prev_result=VerifyCommandResult(
            total_seconds=1.0,
            files={
                pathlib.Path("test/foo.py"): FileResult(
                    content_hash="hash-foo",
                    testdata_hash="testdata-foo",
                    verifications=[
                        VerificationResult(
                            status=SUCCESS,
                            elapsed=1.0,
                            last_execution_time=datetime.datetime(2006, 1, 2),
                        )
                    ],
                )
            },
        ),
        file_hashes={"test/foo.py": "hash-foo"},
        change_detection=change_detection,
    )
    result = verifier.verify(download=download)

    assert result.files[pathlib.Path("test/foo.py")].verifications[0].status == SUCCESS
    assert update.call_count == (1 if download else 0)
    if download:
        assert mock_sync.synced_before_hash == [1]
    mock_sync.run_download.assert_not_called()
