import contextlib
import dataclasses
import datetime
import json
import os
import pathlib
import random
import re
import shutil
from collections.abc import Callable, Generator

import pytest

from competitive_verifier import app
from competitive_verifier.models import (
    FileResult,
    JudgeStatus,
    ResultStatus,
    VerificationResult,
)
from competitive_verifier.models import TestcaseResult as _TestcaseResult
from competitive_verifier.verify import verifier

from .data.integration_data import IntegrationData
from .data.user_defined_and_python import UserDefinedAndPythonData

_HASH_MODE_FILES = {
    pathlib.Path(p)
    for p in (
        "awk/aplusb.test.awk",
        "awk/aplusb_direct.awk",
        "awk/myaplusb1.test.awk",
        "awk/myaplusb2.test.awk",
        "awk/myaplusb3.test.awk",
        "python/failure.mle.py",
        "python/failure.re.py",
        "python/failure.tle.py",
        "python/failure.wa.py",
        "python/skip.py",
        "python/success1.py",
        "python/success2.py",
    )
}
_HASH_MODE_NOT_SUCCESS = {
    pathlib.Path(p)
    for p in (
        "python/failure.mle.py",
        "python/failure.re.py",
        "python/failure.tle.py",
        "python/failure.wa.py",
        "python/skip.py",
    )
}
_HASH_MODE_SUCCESS = _HASH_MODE_FILES - _HASH_MODE_NOT_SUCCESS
_APLUSB_AWK_DEPENDANTS = {
    pathlib.Path(p)
    for p in (
        "awk/aplusb.test.awk",
        "awk/myaplusb1.test.awk",
        "awk/myaplusb2.test.awk",
        "awk/myaplusb3.test.awk",
    )
}


@dataclasses.dataclass(frozen=True)
class HashModeCase:
    """A ``--change-detection hash`` run against the result of an unchanged run.

    Files whose previous result isn't a success are always re-verified;
    ``reverified`` lists the successful files expected to be re-verified too.
    """

    reverified: set[pathlib.Path]
    hash_changed: bool = False
    prev_result: Callable[
        [verifier.VerifyCommandResult], verifier.VerifyCommandResult
    ] = lambda r: r
    args: tuple[str, ...] = ()
    change: tuple[pathlib.Path, bytes] | None = None


def _with_hashes(
    path: str, **hashes: str | None
) -> Callable[[verifier.VerifyCommandResult], verifier.VerifyCommandResult]:
    def rewrite(result: verifier.VerifyCommandResult) -> verifier.VerifyCommandResult:
        file_result = result.files[pathlib.Path(path)]
        for name, value in hashes.items():
            setattr(file_result, name, value)
        return result

    return rewrite


_hash_mode_cases: dict[str, HashModeCase] = {
    "unchanged": HashModeCase(reverified=set()),
    "stale_hash": HashModeCase(
        reverified={pathlib.Path("awk/aplusb.test.awk")},
        prev_result=_with_hashes("awk/aplusb.test.awk", content_hash="0" * 64),
    ),
    "missing_hash": HashModeCase(
        reverified={pathlib.Path("python/success1.py")},
        prev_result=_with_hashes("python/success1.py", content_hash=None),
    ),
    "dependency": HashModeCase(
        reverified=_APLUSB_AWK_DEPENDANTS,
        hash_changed=True,
        change=(pathlib.Path("awk/aplusb.awk"), b"\n# changed\n"),
    ),
}


@pytest.mark.integration
@pytest.mark.usefixtures("additional_path")
@pytest.mark.order(-500)
class TestCommandVerfy:
    @pytest.mark.usefixtures("mock_verification")
    def test_mock_dump(self):
        for _ in range(20):
            command_result = verifier.VerifyCommandResult(
                total_seconds=3,
                files={
                    pathlib.Path("foo/bar.py"): FileResult(
                        verifications=[
                            VerificationResult(
                                verification_name="name1",
                                elapsed=random.randint(10, 242),
                                status=ResultStatus.SUCCESS,
                                last_execution_time=datetime.datetime.fromtimestamp(
                                    random.randint(1000000000, 3000000000)
                                ),
                            ),
                            VerificationResult(
                                verification_name="name2",
                                elapsed=random.randint(10, 242),
                                status=ResultStatus.SKIPPED,
                                heaviest=random.randint(1000, 3000),
                                slowest=random.randint(234, 1234),
                                last_execution_time=datetime.datetime.fromtimestamp(
                                    random.randint(1000000000, 3000000000)
                                ),
                                testcases=[
                                    _TestcaseResult(
                                        name="case01",
                                        status=JudgeStatus.AC,
                                        elapsed=random.randint(12, 24),
                                        memory=random.randint(100, 1000),
                                    ),
                                    _TestcaseResult(
                                        name="case02",
                                        status=JudgeStatus.RE,
                                        elapsed=random.randint(12, 24),
                                        memory=random.randint(100, 1000),
                                    ),
                                    _TestcaseResult(
                                        name="case03",
                                        status=JudgeStatus.WA,
                                        elapsed=random.randint(12, 24),
                                        memory=random.randint(100, 1000),
                                    ),
                                    _TestcaseResult(
                                        name="case04",
                                        status=JudgeStatus.TLE,
                                        elapsed=random.randint(12, 24),
                                        memory=random.randint(100, 1000),
                                    ),
                                ],
                            ),
                        ]
                    ),
                    pathlib.Path("foo/baz2.py"): FileResult(
                        verifications=[
                            VerificationResult(
                                verification_name="name1",
                                elapsed=random.randint(10, 242),
                                status=ResultStatus.SUCCESS,
                                last_execution_time=datetime.datetime.fromtimestamp(
                                    random.randint(1000000000, 3000000000)
                                ),
                            ),
                        ]
                    ),
                },
            )
            assert json.loads(command_result.model_dump_json(exclude_none=True)) == {
                "total_seconds": 2547.12,
                "files": {
                    "foo/bar.py": {
                        "verifications": [
                            {
                                "verification_name": "name1",
                                "status": "success",
                                "elapsed": 9948.0,
                                "last_execution_time": "2004-10-09T00:26:13.890000+02:00",
                            },
                            {
                                "verification_name": "name2",
                                "status": "skipped",
                                "elapsed": 2238.0,
                                "slowest": 223.0,
                                "heaviest": 753.0,
                                "testcases": [
                                    {
                                        "name": "case01",
                                        "status": "AC",
                                        "elapsed": 1.33,
                                        "memory": 32.38,
                                    },
                                    {
                                        "name": "case02",
                                        "status": "RE",
                                        "elapsed": 4.73,
                                        "memory": 9.88,
                                    },
                                    {
                                        "name": "case03",
                                        "status": "WA",
                                        "elapsed": 2.4,
                                        "memory": 35.43,
                                    },
                                    {
                                        "name": "case04",
                                        "status": "TLE",
                                        "elapsed": 2.42,
                                        "memory": 22.41,
                                    },
                                ],
                                "last_execution_time": "2026-11-12T22:34:03.760000-11:00",
                            },
                        ],
                        "newest": True,
                    },
                    "foo/baz2.py": {
                        "verifications": [
                            {
                                "verification_name": "name1",
                                "status": "success",
                                "elapsed": 1239.0,
                                "last_execution_time": "1975-10-05T09:39:58.780000-09:00",
                            }
                        ],
                        "newest": True,
                    },
                },
            }

    @pytest.mark.usefixtures("mock_verification")
    def test_verify(
        self,
        integration_data: IntegrationData,
    ):
        verify = integration_data.config_dir_path / "verify.json"
        result = integration_data.config_dir_path / "result.json"
        shutil.rmtree(integration_data.config_dir_path / "cache", ignore_errors=True)

        parsed = app.ArgumentParser().parse(
            ["verify", "--verify-json", str(verify), "--output", str(result)]
        )
        assert isinstance(parsed, app.Verify)
        assert parsed.run()

        assert (
            json.loads(pathlib.Path(result).read_bytes())
            == integration_data.expected_verify_result()
        )

    @pytest.mark.usefixtures("mock_clone_library_checker")
    @pytest.mark.parametrize("case", _hash_mode_cases.values(), ids=_hash_mode_cases)
    def test_verify_change_detection_hash(
        self,
        user_defined_and_python_data: UserDefinedAndPythonData,
        case: HashModeCase,
    ):
        config_dir = user_defined_and_python_data.config_dir_path
        verify = config_dir / "verify.json"

        first = self._run_verify_hash(verify, config_dir / "result_hash_first.json")
        assert first.files.keys() == _HASH_MODE_FILES
        assert all(f.newest for f in first.files.values())
        assert {
            p for p, f in first.files.items() if not f.is_success(allow_skip=False)
        } == _HASH_MODE_NOT_SUCCESS
        for file_result in first.files.values():
            assert file_result.content_hash
            assert re.fullmatch(r"[0-9a-f]{64}", file_result.content_hash)

        prev_result = case.prev_result(first.model_copy(deep=True))
        prev_path = config_dir / "result_hash_prev.json"
        prev_path.write_text(
            prev_result.model_dump_json(exclude_none=True), encoding="utf-8"
        )
        with self._appended(*case.change) if case.change else contextlib.nullcontext():
            second = self._run_verify_hash(
                verify, config_dir / "result_hash_second.json", prev_path, *case.args
            )

        assert second.files.keys() == first.files.keys()
        assert {
            p for p, f in second.files.items() if f.newest
        } == case.reverified | _HASH_MODE_NOT_SUCCESS
        for path, file_result in second.files.items():
            prev = first.files[path]
            if path in case.reverified:
                assert (
                    file_result.content_hash != prev.content_hash
                ) == case.hash_changed
            elif not file_result.newest:
                assert file_result.content_hash == prev.content_hash
                assert file_result.verifications == prev.verifications

    @staticmethod
    def _run_verify_hash(
        verify: pathlib.Path,
        output: pathlib.Path,
        prev_result: pathlib.Path | None = None,
        *extra_args: str,
    ) -> verifier.VerifyCommandResult:
        args = [
            "verify",
            "--verify-json",
            str(verify),
            "--output",
            str(output),
            "--change-detection",
            "hash",
            *extra_args,
        ]
        if prev_result:
            args.extend(["--prev-result", str(prev_result)])
        parsed = app.ArgumentParser().parse(args)
        assert isinstance(parsed, app.Verify)
        assert parsed.change_detection == "hash"
        assert parsed.run()
        return verifier.VerifyCommandResult.parse_file_relative(output)

    @staticmethod
    @contextlib.contextmanager
    def _appended(path: pathlib.Path, data: bytes) -> Generator[None, None, None]:
        original = path.read_bytes()
        stat = path.stat()
        path.write_bytes(original + data)
        try:
            yield
        finally:
            path.write_bytes(original)
            os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns))
