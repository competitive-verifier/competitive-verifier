import datetime
import json
import pathlib
import random
import shutil
from typing import Any, Generator, List

import onlinejudge.dispatch
import onlinejudge.service.library_checker as library_checker
import pytest
import requests
from onlinejudge.type import TestCase as OjTestCase
from pytest_mock import MockerFixture

import competitive_verifier.config as config
from competitive_verifier.models import FileResult, JudgeStatus, ResultStatus
from competitive_verifier.models import TestcaseResult as _TestcaseResult
from competitive_verifier.models import VerificationResult
from competitive_verifier.verify import main, verifier
from tests.integration.utils import md5_number

from .data.integration_data import IntegrationData


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

    @pytest.mark.each_language_integration
    @pytest.mark.integration
    @pytest.mark.usefixtures("mock_verification")
    def test_verify(
        self,
        integration_data: IntegrationData,
    ):
        verify = integration_data.config_dir_path / "verify.json"
        result = integration_data.config_dir_path / "result.json"
        main.main(["--verify-json", str(verify), "--output", str(result)])

        assert (
            json.loads(pathlib.Path(result).read_bytes())
            == integration_data.expected_verify_result()
        )


class _MockVerifyCommandResult(verifier.VerifyCommandResult):
    def model_dump_json(
        self,
        *,
        indent: Any = None,
        include: Any = None,
        exclude: Any = None,
        by_alias: bool = False,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
        round_trip: bool = False,
        warnings: bool = True,
    ) -> str:
        return self.model_copy()._dump_super(
            indent=indent,
            include=include,
            exclude=exclude,
            by_alias=by_alias,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
            round_trip=round_trip,
            warnings=warnings,
        )

    def _dump_super(
        self,
        *,
        indent: Any = None,
        include: Any = None,
        exclude: Any = None,
        by_alias: bool = False,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
        round_trip: bool = False,
        warnings: bool = True,
    ) -> str:
        def rewriteVerifyCommandResult(result: verifier.VerifyCommandResult):
            result.total_seconds = len(result.files) * 1234.56 + 78
            result.files = {k: rewriteFileResult(k, v) for k, v in result.files.items()}
            return result

        def rewriteFileResult(path: pathlib.Path, file_result: FileResult):
            seed = path.as_posix().encode()
            file_result.verifications = [
                rewriteVerificationResult(seed, v) for v in file_result.verifications
            ]
            return file_result

        def rewriteVerificationResult(seed: bytes, verification: VerificationResult):
            seed += (verification.verification_name or "").encode()
            seed += verification.status.name.encode()

            verification.elapsed = md5_number(seed + b"elapsed") % 10000

            if verification.slowest:
                verification.slowest = verification.elapsed // 10
            if verification.heaviest:
                verification.heaviest = md5_number(seed + b"heaviest") % 1000

            if verification.testcases:
                verification.testcases = [
                    rewriteTestcaseResult(seed, c) for c in verification.testcases
                ]

            random_time = md5_number(seed + b"last_execution_time")
            verification.last_execution_time = datetime.datetime.fromtimestamp(
                random_time % 300000000000 / 100,
                tz=datetime.timezone(datetime.timedelta(hours=random_time % 25 - 12)),
            )

            return verification

        def rewriteTestcaseResult(seed: bytes, case: _TestcaseResult):
            seed += (case.name or "").encode()
            seed += case.status.name.encode()

            case.elapsed = md5_number(seed + b"elapsed") % 1000 / 100
            case.memory = md5_number(seed + b"memory") % 10000 / 100
            return case

        rewriteVerifyCommandResult(self)
        return super().model_dump_json(
            indent=indent,
            include=include,
            exclude=exclude,
            by_alias=by_alias,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
            round_trip=round_trip,
            warnings=warnings,
        )


class _MockLibraryCheckerProblem(library_checker.LibraryCheckerProblem):
    def __init__(self, *, problem_id: str):
        super().__init__(problem_id=problem_id)

    def download_system_cases(self, *, session: Any = None) -> List[OjTestCase]:
        self._update_cloned_repository()
        return list(self._mock_cases())

    def download_sample_cases(self, *, session: Any = None) -> List[OjTestCase]:
        assert False

    def _update_cloned_repository(self) -> None:
        zip_path = config.get_cache_dir() / "library-checker-problems.zip"
        if not zip_path.exists():
            zip_path.parent.mkdir(parents=True, exist_ok=True)
            res = requests.get(
                "https://github.com/yosupo06/library-checker-problems/archive/refs/heads/master.zip"
            )
            with zip_path.open("wb") as fp:
                fp.write(res.content)
            shutil.unpack_archive(zip_path, config.get_cache_dir())
            shutil.move(
                config.get_cache_dir() / "library-checker-problems-master",
                config.get_cache_dir() / "library-checker-problems",
            )

        # library_checker.LibraryCheckerService._update_cloned_repository()  # pyright: ignore[reportPrivateUsage]

    def _mock_cases(self) -> Generator[OjTestCase, Any, Any]:
        if self.problem_id == "aplusb":
            for name, a, b in [
                ("example_00", 1000, 10),
                ("example_01", 1002, 20),
                ("random_00", 1000, 130),
                ("random_01", 1003, 140),
                ("random_02", 1005, 150),
                ("random_03", 1000, 160),
                ("random_04", 1005, 170),
                ("random_05", 1007, 180),
                ("random_06", 1009, 191),
                ("random_07", 1008, 200),
                ("random_08", 1005, 214),
                ("random_09", 1008, 225),
            ]:
                yield OjTestCase(
                    name=name,
                    input_name=f"{name}.in",
                    output_name=f"{name}.out",
                    input_data=f"{a} {b}\n".encode(),
                    output_data=f"{a+b}\n".encode(),
                )
        else:
            raise NotImplementedError()


@pytest.fixture
def mock_verification(mocker: MockerFixture):
    mocker.patch(
        "competitive_verifier.verify.verifier.VerifyCommandResult",
        side_effect=_MockVerifyCommandResult,
    )

    mocker.patch.object(
        onlinejudge.dispatch,
        "problems",
        new=[
            _MockLibraryCheckerProblem
            if p == library_checker.LibraryCheckerProblem
            else p
            for p in onlinejudge.dispatch.problems
        ],
    )
