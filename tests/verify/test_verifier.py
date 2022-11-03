# pyright: reportPrivateUsage=none
import datetime
from pathlib import Path
from typing import Iterable, Optional

import pytest

from competitive_verifier.error import VerifierError
from competitive_verifier.models.command import VerificationCommand
from competitive_verifier.models.file import VerificationFile, VerificationInput
from competitive_verifier.models.result import (
    FileVerificationResult,
    ResultStatus,
    VerificationResult,
)
from competitive_verifier.verify.verifier import SplitState, Verifier


class VerifierForTest(Verifier):
    def __init__(
        self,
        result: VerificationResult,
        input: VerificationInput = VerificationInput(files=[]),
        *,
        use_git_timestamp: bool = True,
        timeout: float = 60,
        default_tle: float = 60,
        prev_result: Optional[VerificationResult] = None,
        split_state: Optional[SplitState] = None,
        verification_time: datetime.datetime = datetime.datetime.max,
        current_timestamp_dict: dict[Optional[Path], datetime.datetime] = {},
    ) -> None:
        super().__init__(
            input=input,
            use_git_timestamp=use_git_timestamp,
            timeout=timeout,
            default_tle=default_tle,
            prev_result=prev_result,
            split_state=split_state,
            verification_time=verification_time,
        )
        self._result = result
        self.current_timestamp_dict = current_timestamp_dict

    def get_current_timestamp(self, path: Path) -> datetime.datetime:
        return self.current_timestamp_dict.get(path, self.current_timestamp_dict[None])


def get_verifier(
    input: VerificationInput = VerificationInput(files=[]),
    *,
    use_git_timestamp: bool = True,
    timeout: float = 60,
    default_tle: float = 60,
    prev_result: Optional[VerificationResult] = None,
    split_state: Optional[SplitState] = None,
    verification_time: Optional[datetime.datetime] = None,
) -> Verifier:
    return Verifier(
        input=input,
        use_git_timestamp=use_git_timestamp,
        timeout=timeout,
        default_tle=default_tle,
        prev_result=prev_result,
        split_state=split_state,
        verification_time=verification_time,
    )


def test_force_result():
    verifier = get_verifier()
    verifier._result = VerificationResult(files=[])
    assert verifier.force_result is verifier._result


def test_force_result_failue():
    verifier = get_verifier()
    with pytest.raises(VerifierError) as e:
        _ = verifier.force_result

    assert e.value.message == "Not verified yet."


def test_verification_files():
    def get_verification_file(path_str: str) -> VerificationFile:
        return VerificationFile(
            path=Path(path_str),
            dependencies=[],
            verification=[VerificationCommand(command="true")],
        )

    foo_baz = get_verification_file("foo/baz.py")
    foo_abc = get_verification_file("foo/abc.py")
    baz_foo = get_verification_file("baz/foo.py")
    hoge_piyo = get_verification_file("hoge/piyo.py")
    hoge_hoge = get_verification_file("hoge/hoge.py")
    verifier = get_verifier(
        input=VerificationInput(
            files=[
                foo_baz,
                foo_abc,
                baz_foo,
                hoge_piyo,
                hoge_hoge,
            ]
        ),
    )
    assert verifier.verification_files == [
        baz_foo,
        foo_abc,
        foo_baz,
        hoge_hoge,
        hoge_piyo,
    ]


def test_remaining_verification_files():
    def get_verification_file(path_str: str) -> VerificationFile:
        return VerificationFile(
            path=Path(path_str),
            dependencies=[],
            verification=[VerificationCommand(command="true")],
        )

    foo_baz = get_verification_file("foo/baz.py")
    foo_abc = get_verification_file("foo/abc.py")
    baz_foo = get_verification_file("baz/foo.py")
    hoge_piyo = get_verification_file("hoge/piyo.py")
    hoge_hoge = get_verification_file("hoge/hoge.py")
    verifier = VerifierForTest(
        VerificationResult(files=[]),
        VerificationInput(
            files=[
                baz_foo,
                foo_abc,
                foo_baz,
                hoge_hoge,
                hoge_piyo,
            ]
        ),
        verification_time=datetime.datetime(2020, 2, 27, 19, 0, 0),
        current_timestamp_dict={
            None: datetime.datetime(2019, 12, 25, 19, 0, 0),
            Path("hoge/piyo.py"): datetime.datetime(2019, 12, 28, 19, 0, 0),
            Path("hoge/hoge.py"): datetime.datetime(2019, 12, 27, 19, 0, 0),
        },
        prev_result=VerificationResult(
            files=[
                FileVerificationResult(
                    path=baz_foo.path,
                    last_success_time=None,
                    command_result=ResultStatus.SUCCESS,
                ),
                FileVerificationResult(
                    path=hoge_hoge.path,
                    last_success_time=datetime.datetime(2019, 12, 27, 19, 0, 0),
                    command_result=ResultStatus.SUCCESS,
                ),
                FileVerificationResult(
                    path=hoge_piyo.path,
                    last_success_time=datetime.datetime(2019, 12, 27, 19, 0, 0),
                    command_result=ResultStatus.SUCCESS,
                ),
            ]
        ),
    )
    assert verifier.remaining_verification_files == [
        baz_foo,
        foo_abc,
        foo_baz,
        hoge_piyo,
    ]


def generate_current_verification_files() -> Iterable[
    tuple[Verifier, list[VerificationFile]]
]:
    def get_verification_file(path_str: str) -> VerificationFile:
        return VerificationFile(
            path=Path(path_str),
            dependencies=[],
            verification=[VerificationCommand(command="true")],
        )

    foo_baz = get_verification_file("foo/baz.py")
    foo_abc = get_verification_file("foo/abc.py")
    baz_foo = get_verification_file("baz/foo.py")
    hoge_piyo = get_verification_file("hoge/piyo.py")
    hoge_hoge = get_verification_file("hoge/hoge.py")

    def get_verifier_with_split_state(state: Optional[SplitState]):
        return VerifierForTest(
            VerificationResult(files=[]),
            VerificationInput(
                files=[
                    baz_foo,
                    foo_abc,
                    foo_baz,
                    hoge_hoge,
                    hoge_piyo,
                ]
            ),
            verification_time=datetime.datetime(2020, 2, 27, 19, 0, 0),
            current_timestamp_dict={
                None: datetime.datetime(2019, 12, 25, 19, 0, 0),
                Path("hoge/piyo.py"): datetime.datetime(2019, 12, 28, 19, 0, 0),
                Path("hoge/hoge.py"): datetime.datetime(2019, 12, 27, 19, 0, 0),
            },
            prev_result=VerificationResult(
                files=[
                    FileVerificationResult(
                        path=baz_foo.path,
                        last_success_time=None,
                        command_result=ResultStatus.SUCCESS,
                    ),
                    FileVerificationResult(
                        path=hoge_hoge.path,
                        last_success_time=datetime.datetime(2019, 12, 27, 19, 0, 0),
                        command_result=ResultStatus.SUCCESS,
                    ),
                    FileVerificationResult(
                        path=hoge_piyo.path,
                        last_success_time=datetime.datetime(2019, 12, 27, 19, 0, 0),
                        command_result=ResultStatus.SUCCESS,
                    ),
                ]
            ),
            split_state=state,
        )

    yield get_verifier_with_split_state(None), [
        baz_foo,
        foo_abc,
        foo_baz,
        hoge_piyo,
    ]

    yield get_verifier_with_split_state(SplitState(size=3, index=0)), [
        baz_foo,
    ]

    yield get_verifier_with_split_state(SplitState(size=3, index=1)), [
        foo_abc,
    ]

    yield get_verifier_with_split_state(SplitState(size=3, index=2)), [
        foo_baz,
        hoge_piyo,
    ]


current_verification_files_params = list(generate_current_verification_files())


@pytest.mark.parametrize(
    "verifier, expected",
    current_verification_files_params,
    ids=[f"{tup[0]}" for tup in current_verification_files_params],
)
def test_current_verification_files(
    verifier: Verifier, expected: list[VerificationFile]
):
    assert verifier.current_verification_files == expected


def test_is_success():
    def get_result(
        path: str, *, command_result: ResultStatus = ResultStatus.SUCCESS
    ) -> FileVerificationResult:
        return FileVerificationResult(
            path=Path(path),
            last_success_time=datetime.datetime(2017, 9, 20, 18, 0, 0),
            command_result=command_result,
        )

    verifier = VerifierForTest(
        VerificationResult(
            files=[
                get_result("lib/bar.py"),
                get_result("lib/baz.py"),
                get_result("lib/hoge.py"),
                get_result("lib/fuga.py"),
                get_result("test/1.py"),
                get_result("test/2.py"),
                get_result("test/3.py"),
                get_result("test/4.py"),
            ]
        )
    )
    assert verifier.is_success()

    verifier = VerifierForTest(
        VerificationResult(
            files=[
                get_result("lib/bar.py"),
                get_result("lib/baz.py"),
                get_result("lib/hoge.py"),
                get_result("lib/fuga.py"),
                get_result("test/1.py"),
                get_result("test/2.py"),
                get_result("test/3.py"),
                get_result("test/4.py", command_result=ResultStatus.FAILURE),
            ]
        )
    )
    assert not verifier.is_success()
