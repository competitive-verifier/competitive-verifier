import datetime
import pathlib

import pytest

from competitive_verifier.models.file import VerificationFiles
from competitive_verifier.models.result import (
    FileVerificationResult,
    VerificationResult,
)
from competitive_verifier.verify.util import VerifyError
from competitive_verifier.verify.verifier import Verifier


def test_result():
    verifier = Verifier(
        files=VerificationFiles(files=[]),
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


class VerifierForIsSuccessTest(Verifier):
    def __init__(
        self,
        result: VerificationResult,
        verification_time: datetime.datetime,
        default_current_timestamp: datetime.datetime,
        current_timestamp_dict: dict[pathlib.Path, datetime.datetime],
    ) -> None:
        super().__init__(
            files=VerificationFiles(files=[]),
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

    def get_current_timestamp(self, path: pathlib.Path) -> datetime.datetime:
        return self.current_timestamp_dict.get(path, self.default_current_timestamp)


def test_is_success():
    last_success_time = datetime.datetime(2017, 9, 20, 18, 0, 0)
    res = VerificationResult(
        results=[
            FileVerificationResult(
                pathlib.Path("lib/bar.py"),
                last_success_time=last_success_time,
            ),
            FileVerificationResult(
                pathlib.Path("lib/baz.py"),
                last_success_time=last_success_time,
            ),
            FileVerificationResult(
                pathlib.Path("lib/hoge.py"),
                last_success_time=last_success_time,
            ),
            FileVerificationResult(
                pathlib.Path("lib/fuga.py"),
                last_success_time=last_success_time,
            ),
            FileVerificationResult(
                pathlib.Path("test/1.py"),
                last_success_time=last_success_time,
            ),
            FileVerificationResult(
                pathlib.Path("test/2.py"),
                last_success_time=last_success_time,
            ),
            FileVerificationResult(
                pathlib.Path("test/3.py"),
                last_success_time=last_success_time,
            ),
            FileVerificationResult(
                pathlib.Path("test/4.py"),
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
            pathlib.Path("test/1.py"): datetime.datetime(2018, 12, 24, 18, 36, 45),
        },
    )
    assert not verifier.is_success()
