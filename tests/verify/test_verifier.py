# pyright: reportPrivateUsage=none
import datetime
from pathlib import Path
from typing import Any, Callable, Optional

import pytest

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
from competitive_verifier.verify.verifier import InputContainer, SplitState

SUCCESS = ResultStatus.SUCCESS


class MockInputContainer(InputContainer):
    def __init__(
        self,
        obj: Any = None,
        *,
        prev_result: Optional[VerifyCommandResult] = None,
        verification_time: Optional[datetime.datetime] = None,
        file_timestamps: dict[Optional[Path], datetime.datetime] = {},
        split_state: Optional[SplitState] = None,
    ) -> None:
        super().__init__(
            input=VerificationInput.model_validate(obj) if obj else VerificationInput(),
            verification_time=verification_time or datetime.datetime.now(),
            prev_result=prev_result,
            split_state=split_state,
        )

        self.file_timestamps = file_timestamps

    def get_file_timestamp(self, path: Path) -> datetime.datetime:
        assert self.file_timestamps is not None
        dt = self.file_timestamps.get(path)
        if dt:
            return dt
        return self.file_timestamps[None]


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
    "resolver, expected",
    test_verification_files_params,
    ids=range(len(test_verification_files_params)),
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


@pytest.mark.parametrize(
    "resolver, path, file_result, expected",
    test_file_need_verification_params,
    ids=range(len(test_file_need_verification_params)),
)
def test_file_need_verification(
    resolver: InputContainer,
    path: Path,
    file_result: FileResult,
    expected: bool,
    mock_exists: Callable[[bool], Any],
):
    mock_exists(True)
    assert resolver.file_need_verification(path, file_result) == expected


@pytest.mark.parametrize(
    "resolver, path, file_result, _",
    test_file_need_verification_params,
    ids=range(len(test_file_need_verification_params)),
)
def test_file_need_verification_no_file(
    resolver: InputContainer,
    path: Path,
    file_result: FileResult,
    _: bool,
    mock_exists: Callable[[bool], Any],
):
    mock_exists(False)
    assert not resolver.file_need_verification(path, file_result)


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
            file_timestamps={
                None: datetime.datetime(2018, 5, 22),
            },
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
    "resolver, expected",
    test_remaining_verification_files_params,
    ids=range(len(test_remaining_verification_files_params)),
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
    "index, expected",
    test_current_verification_files_params,
    ids=range(len(test_current_verification_files_params)),
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
