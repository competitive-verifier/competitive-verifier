import datetime
from pathlib import Path

import pytest

from competitive_verifier.models.command import VerificationCommand
from competitive_verifier.models.file import VerificationFile, VerificationInput
from competitive_verifier.models.result import (
    FileVerificationResult,
    VerificationResult,
)
from competitive_verifier.verify.util import VerifyError
from competitive_verifier.verify.verifier import Verifier


def test_force_result():
    verifier = Verifier(
        input=VerificationInput(files=[]),
        default_tle=60,
        timeout=0,
        prev_result=None,
        split_state=None,
        use_git_timestamp=True,
        verification_time=None,
    )
    verifier.result = VerificationResult(results=[])
    assert verifier.force_result is verifier.result


def test_force_result_failue():
    verifier = Verifier(
        input=VerificationInput(files=[]),
        default_tle=60,
        timeout=0,
        prev_result=None,
        split_state=None,
        use_git_timestamp=True,
        verification_time=None,
    )
    with pytest.raises(VerifyError) as e:
        _ = verifier.force_result

    assert e.value.message == "Not verified yet."


def test_verification_files():
    def get_verification_file(path_str: str) -> VerificationFile:
        return VerificationFile(
            Path(path_str),
            dependencies=[],
            verification=VerificationCommand(command="true"),
        )

    foo_baz = get_verification_file("foo/baz.py")
    foo_abc = get_verification_file("foo/abc.py")
    baz_foo = get_verification_file("baz/foo.py")
    hoge_piyo = get_verification_file("hoge/piyo.py")
    hoge_hoge = get_verification_file("hoge/hoge.py")
    verifier = Verifier(
        input=VerificationInput(
            files=[
                foo_baz,
                foo_abc,
                baz_foo,
                hoge_piyo,
                hoge_hoge,
            ]
        ),
        default_tle=60,
        timeout=0,
        prev_result=None,
        split_state=None,
        use_git_timestamp=True,
        verification_time=None,
    )
    assert verifier.verification_files == [
        baz_foo,
        foo_abc,
        foo_baz,
        hoge_hoge,
        hoge_piyo,
    ]


class VerifierForIsSuccessTest(Verifier):
    def __init__(
        self,
        result: VerificationResult,
        verification_time: datetime.datetime,
        default_current_timestamp: datetime.datetime,
        current_timestamp_dict: dict[Path, datetime.datetime],
    ) -> None:
        super().__init__(
            input=VerificationInput(files=[]),
            default_tle=60,
            timeout=0,
            prev_result=None,
            split_state=None,
            use_git_timestamp=True,
            verification_time=verification_time,
        )
        self.result = result
        self.default_current_timestamp = default_current_timestamp
        self.current_timestamp_dict = current_timestamp_dict

    def get_current_timestamp(self, path: Path) -> datetime.datetime:
        return self.current_timestamp_dict.get(path, self.default_current_timestamp)


def test_is_success():
    last_success_time = datetime.datetime(2017, 9, 20, 18, 0, 0)
    res = VerificationResult(
        results=[
            FileVerificationResult(
                Path("lib/bar.py"),
                last_success_time=last_success_time,
            ),
            FileVerificationResult(
                Path("lib/baz.py"),
                last_success_time=last_success_time,
            ),
            FileVerificationResult(
                Path("lib/hoge.py"),
                last_success_time=last_success_time,
            ),
            FileVerificationResult(
                Path("lib/fuga.py"),
                last_success_time=last_success_time,
            ),
            FileVerificationResult(
                Path("test/1.py"),
                last_success_time=last_success_time,
            ),
            FileVerificationResult(
                Path("test/2.py"),
                last_success_time=last_success_time,
            ),
            FileVerificationResult(
                Path("test/3.py"),
                last_success_time=last_success_time,
            ),
            FileVerificationResult(
                Path("test/4.py"),
                last_success_time=last_success_time,
            ),
        ]
    )
    verifier = VerifierForIsSuccessTest(
        res,
        verification_time=datetime.datetime(2017, 9, 20, 18, 0, 1),
        default_current_timestamp=datetime.datetime(2016, 12, 24, 18, 36, 45),
        current_timestamp_dict={},
    )
    assert verifier.is_success()

    verifier = VerifierForIsSuccessTest(
        res,
        verification_time=datetime.datetime(2017, 9, 20, 18, 0, 1),
        default_current_timestamp=datetime.datetime(2019, 12, 24, 18, 36, 45),
        current_timestamp_dict={},
    )
    assert not verifier.is_success()

    verifier = VerifierForIsSuccessTest(
        res,
        verification_time=datetime.datetime(2017, 9, 20, 18, 0, 1),
        default_current_timestamp=datetime.datetime(2016, 12, 24, 18, 36, 45),
        current_timestamp_dict={
            Path("test/1.py"): datetime.datetime(2018, 12, 24, 18, 36, 45),
        },
    )
    assert not verifier.is_success()
