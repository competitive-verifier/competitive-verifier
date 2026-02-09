import datetime
import pathlib
from pathlib import Path
from typing import Any, NamedTuple, cast

import pytest
from pytest_mock import MockerFixture

from competitive_verifier.models import (
    CommandVerification,
    ConstVerification,
    FileResult,
    ResultStatus,
    VerificationFile,
    VerificationInput,
    VerificationResult,
    VerifyCommandResult,
)
from competitive_verifier.verify.verifier import (
    InputContainer,
    SplitState,
    Verifier,
    _now,  # pyright: ignore[reportPrivateUsage]
)

SUCCESS = ResultStatus.SUCCESS


def test_now():
    assert _now().tzinfo is not None


def test_get_file_timestamp_git_timestamp(mocker: MockerFixture):
    verifier = Verifier(
        VerificationInput(),
        timeout=1,
        default_tle=None,
        default_mle=None,
        prev_result=None,
        split_state=None,
        use_git_timestamp=True,
    )
    mocker.patch.dict(
        verifier.verifications.transitive_depends_on,
        {pathlib.Path("foo"): {pathlib.Path("foo"), pathlib.Path("bar")}},
    )

    get_commit_time = mocker.patch(
        "competitive_verifier.git.get_commit_time",
        return_value=datetime.datetime.max,
    )

    assert verifier.get_file_timestamp(pathlib.Path("foo")) == datetime.datetime.max
    get_commit_time.assert_called_once_with({pathlib.Path("foo"), pathlib.Path("bar")})


def test_get_file_timestamp_local(mocker: MockerFixture):
    class MockPath(NamedTuple):
        name: str
        time: datetime.datetime

        @property
        def st_mtime(self) -> float:
            assert self.time.tzinfo == datetime.timezone.utc
            return self.time.timestamp()

        def stat(self):
            return self

    verifier = Verifier(
        VerificationInput(),
        timeout=1,
        default_tle=None,
        default_mle=None,
        prev_result=None,
        split_state=None,
        use_git_timestamp=False,
    )

    foo_path = MockPath(
        "foo",
        datetime.datetime.fromisoformat("2001-02-03T04:05:05.789789+00:00"),
    )
    bar_path = MockPath(
        "bar",
        datetime.datetime.fromisoformat("2001-02-03T04:05:06.789789+00:00"),
    )

    mocker.patch(
        "competitive_verifier.verify.verifier._now",
        return_value=datetime.datetime.fromisoformat(
            "2010-08-31T15:26:56.456797+06:30"
        ),
    )
    mocker.patch.dict(
        verifier.verifications.transitive_depends_on,
        {foo_path: {foo_path, bar_path}},
    )

    get_commit_time = mocker.patch("competitive_verifier.git.get_commit_time")

    assert verifier.get_file_timestamp(
        cast("pathlib.Path", foo_path)
    ) == datetime.datetime.fromisoformat("2001-02-03T10:35:06+06:30")
    get_commit_time.assert_not_called()


class MockInputContainer(InputContainer):
    def __init__(
        self,
        obj: Any = None,
        *,
        prev_result: VerifyCommandResult | None = None,
        verification_time: datetime.datetime | None = None,
        file_timestamps: dict[Path, datetime.datetime] | None = None,
        split_state: SplitState | None = None,
    ) -> None:
        super().__init__(
            verifications=VerificationInput.model_validate(obj)
            if obj
            else VerificationInput(),
            verification_time=verification_time or datetime.datetime.now(),
            prev_result=prev_result,
            split_state=split_state,
        )

        self.file_timestamps = file_timestamps or {}

    def get_file_timestamp(self, path: Path) -> datetime.datetime:
        assert self.file_timestamps is not None
        dt = self.file_timestamps.get(path)
        assert dt is not None
        return dt


test_verification_files_params: list[
    tuple[InputContainer, dict[Path, VerificationFile]]
] = [
    (
        MockInputContainer(
            {
                "files": {
                    "foo": {},
                    "bar": {},
                    "baz": {},
                },
            }
        ),
        {},
    ),
    (
        MockInputContainer(
            {
                "files": {
                    "foo": {
                        "verification": {
                            "type": "const",
                            "status": "success",
                        }
                    },
                    "bar": {
                        "verification": {
                            "type": "const",
                            "status": "success",
                        }
                    },
                    "baz": {
                        "verification": {
                            "type": "const",
                            "status": "success",
                        }
                    },
                },
            }
        ),
        {
            Path("foo"): VerificationFile(
                verification=ConstVerification(status=SUCCESS),
            ),
            Path("bar"): VerificationFile(
                verification=ConstVerification(status=SUCCESS),
            ),
            Path("baz"): VerificationFile(
                verification=ConstVerification(status=SUCCESS),
            ),
        },
    ),
    (
        MockInputContainer(
            {
                "files": {
                    "foo": {
                        "verification": {
                            "type": "const",
                            "status": "success",
                        }
                    },
                    "bar": {},
                    "baz": {
                        "verification": {
                            "type": "const",
                            "status": "success",
                        }
                    },
                },
            }
        ),
        {
            Path("foo"): VerificationFile(
                verification=ConstVerification(status=SUCCESS),
            ),
            Path("baz"): VerificationFile(
                verification=ConstVerification(status=SUCCESS),
            ),
        },
    ),
]


@pytest.mark.parametrize(
    ("resolver", "expected"),
    test_verification_files_params,
)
def test_verification_files(
    resolver: InputContainer,
    expected: dict[Path, VerificationFile],
):
    assert resolver.verification_files == expected


test_file_need_verification_params: list[
    tuple[InputContainer, Path, FileResult, bool]
] = [
    (
        MockInputContainer(
            verification_time=datetime.datetime(2018, 12, 25),
            file_timestamps={
                Path("foo"): datetime.datetime(2015, 12, 25),
            },
        ),
        Path("foo"),
        FileResult(
            verifications=[
                VerificationResult(
                    elapsed=1.5,
                    status=ResultStatus.SUCCESS,
                    last_execution_time=datetime.datetime(2016, 12, 24),
                ),
            ]
        ),
        False,
    ),
    (
        MockInputContainer(
            verification_time=datetime.datetime(2018, 12, 25),
            file_timestamps={
                Path("foo"): datetime.datetime(2017, 12, 25),
            },
        ),
        Path("foo"),
        FileResult(
            verifications=[
                VerificationResult(
                    elapsed=1.5,
                    status=ResultStatus.SUCCESS,
                    last_execution_time=datetime.datetime(2016, 12, 24),
                ),
            ]
        ),
        True,
    ),
    (
        MockInputContainer(
            verification_time=datetime.datetime(2018, 12, 25),
            file_timestamps={
                Path("foo"): datetime.datetime(2015, 12, 25),
            },
        ),
        Path("foo"),
        FileResult(
            verifications=[
                VerificationResult(
                    elapsed=1.5,
                    status=ResultStatus.FAILURE,
                    last_execution_time=datetime.datetime(2016, 12, 24),
                ),
            ]
        ),
        True,
    ),
    (
        MockInputContainer(
            verification_time=datetime.datetime(2018, 12, 25),
            file_timestamps={
                Path("foo"): datetime.datetime(2015, 12, 25),
            },
        ),
        Path("foo"),
        FileResult(
            verifications=[
                VerificationResult(
                    elapsed=1.5,
                    status=ResultStatus.SKIPPED,
                    last_execution_time=datetime.datetime(2016, 12, 24),
                ),
            ]
        ),
        True,
    ),
    (
        MockInputContainer(
            verification_time=datetime.datetime(2018, 12, 25),
            file_timestamps={
                Path("foo"): datetime.datetime(2015, 12, 25),
            },
        ),
        Path("foo"),
        FileResult(
            verifications=[
                VerificationResult(
                    elapsed=1.5,
                    status=ResultStatus.SUCCESS,
                    last_execution_time=datetime.datetime(2016, 12, 24),
                ),
            ]
        ),
        False,
    ),
    (
        MockInputContainer(
            verification_time=datetime.datetime(2015, 12, 25),
            file_timestamps={
                Path("foo"): datetime.datetime(2017, 12, 25),
            },
        ),
        Path("foo"),
        FileResult(
            verifications=[
                VerificationResult(
                    elapsed=1.5,
                    status=ResultStatus.SUCCESS,
                    last_execution_time=datetime.datetime(2016, 12, 24),
                ),
            ]
        ),
        False,
    ),
]


test_remaining_verification_files_params: list[
    tuple[InputContainer, dict[Path, VerificationFile]]
] = [
    (
        MockInputContainer(
            {
                "files": {
                    "foo": {
                        "verification": {
                            "type": "const",
                            "status": "success",
                        }
                    },
                    "bar": {
                        "verification": {
                            "type": "const",
                            "status": "success",
                        }
                    },
                    "baz": {
                        "verification": {
                            "type": "const",
                            "status": "success",
                        }
                    },
                },
            }
        ),
        {},
    ),
    (
        MockInputContainer(
            {
                "files": {
                    "foo": {"verification": {"type": "command", "command": "true"}},
                    "bar": {
                        "verification": {
                            "type": "const",
                            "status": "success",
                        }
                    },
                    "baz": {"verification": {"type": "command", "command": "true"}},
                },
            }
        ),
        {
            Path("foo"): VerificationFile(
                verification=CommandVerification(command="true"),
            ),
            Path("baz"): VerificationFile(
                verification=CommandVerification(command="true"),
            ),
        },
    ),
    (
        MockInputContainer(
            {
                "files": {
                    "foo": {"verification": {"type": "command", "command": "true"}},
                    "bar": {
                        "verification": {
                            "type": "const",
                            "status": "success",
                        }
                    },
                    "baz": {"verification": {"type": "command", "command": "true"}},
                },
            },
            verification_time=datetime.datetime(9999, 5, 22),
            prev_result=VerifyCommandResult(
                total_seconds=1.5,
                files={
                    Path("baz"): FileResult(
                        verifications=[
                            VerificationResult(
                                elapsed=1.5,
                                status=ResultStatus.SUCCESS,
                                last_execution_time=datetime.datetime(2018, 7, 22),
                            )
                        ]
                    )
                },
            ),
        ),
        {
            Path("foo"): VerificationFile(
                verification=CommandVerification(command="true"),
            ),
        },
    ),
]


@pytest.mark.parametrize(
    ("resolver", "expected"),
    test_remaining_verification_files_params,
)
def test_remaining_verification_files(
    resolver: InputContainer,
    expected: dict[Path, VerificationFile],
):
    assert resolver.remaining_verification_files == expected


test_current_verification_files_params: list[
    tuple[int, dict[Path, VerificationFile]]
] = [
    (
        0,
        {
            Path("bar/0.py"): VerificationFile(
                verification=CommandVerification(command="true"),
            ),
            Path("bar/1.py"): VerificationFile(
                verification=CommandVerification(command="true"),
            ),
            Path("bar/2.py"): VerificationFile(
                verification=CommandVerification(command="true"),
            ),
        },
    ),
    (
        1,
        {
            Path("bar/3.py"): VerificationFile(
                verification=CommandVerification(command="true"),
            ),
            Path("baz/0.py"): VerificationFile(
                verification=CommandVerification(command="true"),
            ),
            Path("baz/1.py"): VerificationFile(
                verification=CommandVerification(command="true"),
            ),
        },
    ),
    (
        2,
        {
            Path("baz/2.py"): VerificationFile(
                verification=CommandVerification(command="true"),
            ),
            Path("baz/3.py"): VerificationFile(
                verification=CommandVerification(command="true"),
            ),
            Path("foo/0.py"): VerificationFile(
                verification=CommandVerification(command="true"),
            ),
        },
    ),
    (
        3,
        {
            Path("foo/1.py"): VerificationFile(
                verification=CommandVerification(command="true"),
            ),
            Path("foo/2.py"): VerificationFile(
                verification=CommandVerification(command="true"),
            ),
            Path("foo/3.py"): VerificationFile(
                verification=CommandVerification(command="true"),
            ),
        },
    ),
    (
        4,
        {},
    ),
]


@pytest.mark.parametrize(
    ("resolver", "path", "file_result", "expected"),
    test_file_need_verification_params,
)
def test_file_need_verification(
    resolver: InputContainer,
    path: Path,
    file_result: FileResult,
    expected: bool,
    mocker: MockerFixture,
):
    mocker.patch.object(pathlib.Path, "exists", return_value=True)
    assert resolver.file_need_verification(path, file_result) == expected

    mocker.patch.object(pathlib.Path, "exists", return_value=False)
    assert not resolver.file_need_verification(path, file_result)


@pytest.mark.parametrize(
    ("index", "expected"),
    test_current_verification_files_params,
)
def test_current_verification_files(index: int, expected: dict[Path, VerificationFile]):
    command_verification = {"verification": {"type": "command", "command": "true"}}
    resolver = MockInputContainer(
        {
            "files": {
                "dummy/0.py": {},
                "foo/0.py": command_verification,
                "bar/0.py": command_verification,
                "baz/0.py": command_verification,
                "dummy/1.py": {},
                "foo/1.py": command_verification,
                "bar/1.py": command_verification,
                "baz/1.py": command_verification,
                "foo/2.py": command_verification,
                "dummy/2.py": {},
                "bar/2.py": command_verification,
                "baz/2.py": command_verification,
                "baz/3.py": command_verification,
                "dummy/3.py": {},
                "bar/3.py": command_verification,
                "foo/3.py": command_verification,
            },
        },
        split_state=SplitState(size=4, index=index),
    )
    remaining_verification_files = {
        Path("foo/0.py"): VerificationFile(
            verification=CommandVerification(command="true"),
        ),
        Path("bar/0.py"): VerificationFile(
            verification=CommandVerification(command="true"),
        ),
        Path("baz/0.py"): VerificationFile(
            verification=CommandVerification(command="true"),
        ),
        Path("foo/1.py"): VerificationFile(
            verification=CommandVerification(command="true"),
        ),
        Path("bar/1.py"): VerificationFile(
            verification=CommandVerification(command="true"),
        ),
        Path("baz/1.py"): VerificationFile(
            verification=CommandVerification(command="true"),
        ),
        Path("foo/2.py"): VerificationFile(
            verification=CommandVerification(command="true"),
        ),
        Path("bar/2.py"): VerificationFile(
            verification=CommandVerification(command="true"),
        ),
        Path("baz/2.py"): VerificationFile(
            verification=CommandVerification(command="true"),
        ),
        Path("foo/3.py"): VerificationFile(
            verification=CommandVerification(command="true"),
        ),
        Path("bar/3.py"): VerificationFile(
            verification=CommandVerification(command="true"),
        ),
        Path("baz/3.py"): VerificationFile(
            verification=CommandVerification(command="true"),
        ),
    }
    assert resolver.remaining_verification_files == remaining_verification_files
    assert resolver.current_verification_files == expected
