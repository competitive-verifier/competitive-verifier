import datetime
import json
import pathlib
import random
from typing import Any, Generator, List

import onlinejudge.dispatch
import onlinejudge.service.library_checker as library_checker
import pytest
from onlinejudge.type import TestCase as OjTestCase
from pytest_mock import MockerFixture

from competitive_verifier.models import FileResult, JudgeStatus, ResultStatus
from competitive_verifier.models import TestcaseResult as _TestcaseResult
from competitive_verifier.models import VerificationResult
from competitive_verifier.oj_test_command import check_gnu_time
from competitive_verifier.verify import main, verifier
from tests.integration.utils import md5_number

from .types import ConfigDirFunc, FilePaths


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
        library_checker.LibraryCheckerService._update_cloned_repository()  # pyright: ignore[reportPrivateUsage]

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


class VerifyData(FilePaths):
    pass


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


@pytest.fixture
def data(file_paths: FilePaths) -> VerifyData:
    return VerifyData.model_validate(file_paths.model_dump())


@pytest.mark.usefixtures("mock_verification")
def test_mock_dump():
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


@pytest.mark.integration
@pytest.mark.dependency(
    name="verify_default",
    depends=["resolve_default"],
    scope="package",
)
@pytest.mark.usefixtures("mock_verification")
def test_verify(
    data: VerifyData,
    config_dir: ConfigDirFunc,
):
    config_dir("integration")
    main.main(["--verify-json", data.verify, "--output", data.result])
    assert json.loads(pathlib.Path(data.result).read_bytes()) == {
        "total_seconds": 8719.92,
        "files": {
            "targets/python/failure.mle.py": {
                "verifications": [
                    {
                        "verification_name": "Python",
                        "status": "failure",
                        "elapsed": 961.0,
                        "last_execution_time": "1986-01-16T01:09:24.400000+03:00",
                        **(
                            {
                                "slowest": 96.0,
                                "heaviest": 751.0,
                                "testcases": [
                                    {
                                        "name": "example_00",
                                        "status": "MLE",
                                        "elapsed": 6.26,
                                        "memory": 60.26,
                                    },
                                    {
                                        "name": "example_01",
                                        "status": "MLE",
                                        "elapsed": 2.4,
                                        "memory": 59.44,
                                    },
                                    {
                                        "name": "random_00",
                                        "status": "MLE",
                                        "elapsed": 6.48,
                                        "memory": 7.31,
                                    },
                                    {
                                        "name": "random_01",
                                        "status": "AC",
                                        "elapsed": 9.73,
                                        "memory": 24.23,
                                    },
                                    {
                                        "name": "random_02",
                                        "status": "AC",
                                        "elapsed": 4.88,
                                        "memory": 52.64,
                                    },
                                    {
                                        "name": "random_03",
                                        "status": "MLE",
                                        "elapsed": 0.47,
                                        "memory": 29.96,
                                    },
                                    {
                                        "name": "random_04",
                                        "status": "AC",
                                        "elapsed": 7.88,
                                        "memory": 34.93,
                                    },
                                    {
                                        "name": "random_05",
                                        "status": "AC",
                                        "elapsed": 8.89,
                                        "memory": 71.35,
                                    },
                                    {
                                        "name": "random_06",
                                        "status": "AC",
                                        "elapsed": 7.13,
                                        "memory": 38.93,
                                    },
                                    {
                                        "name": "random_07",
                                        "status": "MLE",
                                        "elapsed": 5.77,
                                        "memory": 84.25,
                                    },
                                    {
                                        "name": "random_08",
                                        "status": "AC",
                                        "elapsed": 4.06,
                                        "memory": 42.35,
                                    },
                                    {
                                        "name": "random_09",
                                        "status": "MLE",
                                        "elapsed": 1.99,
                                        "memory": 10.53,
                                    },
                                ],
                            }
                            if check_gnu_time()
                            else {}
                        ),
                    }
                ],
                "newest": True,
            },
            "targets/python/failure.wa.py": {
                "verifications": [
                    {
                        "verification_name": "Python",
                        "status": "failure",
                        "elapsed": 101.0,
                        "slowest": 10.0,
                        "heaviest": 892.0,
                        "testcases": [
                            {
                                "name": "example_00",
                                "status": "AC",
                                "elapsed": 8.82,
                                "memory": 90.49,
                            },
                            {
                                "name": "example_01",
                                "status": "AC",
                                "elapsed": 8.18,
                                "memory": 77.99,
                            },
                            {
                                "name": "random_00",
                                "status": "AC",
                                "elapsed": 4.75,
                                "memory": 27.37,
                            },
                            {
                                "name": "random_01",
                                "status": "WA",
                                "elapsed": 0.06,
                                "memory": 86.57,
                            },
                            {
                                "name": "random_02",
                                "status": "WA",
                                "elapsed": 9.79,
                                "memory": 4.53,
                            },
                            {
                                "name": "random_03",
                                "status": "AC",
                                "elapsed": 4.02,
                                "memory": 71.02,
                            },
                            {
                                "name": "random_04",
                                "status": "WA",
                                "elapsed": 9.75,
                                "memory": 55.4,
                            },
                            {
                                "name": "random_05",
                                "status": "WA",
                                "elapsed": 3.46,
                                "memory": 7.43,
                            },
                            {
                                "name": "random_06",
                                "status": "AC",
                                "elapsed": 5.18,
                                "memory": 8.11,
                            },
                            {
                                "name": "random_07",
                                "status": "AC",
                                "elapsed": 3.66,
                                "memory": 31.86,
                            },
                            {
                                "name": "random_08",
                                "status": "WA",
                                "elapsed": 3.82,
                                "memory": 5.56,
                            },
                            {
                                "name": "random_09",
                                "status": "WA",
                                "elapsed": 7.69,
                                "memory": 38.28,
                            },
                        ],
                        "last_execution_time": "2013-12-07T21:38:54.760000-11:00",
                    }
                ],
                "newest": True,
            },
            "targets/python/failure.tle.py": {
                "verifications": [
                    {
                        "verification_name": "Python",
                        "status": "failure",
                        "elapsed": 4292.0,
                        "slowest": 429.0,
                        "heaviest": 661.0,
                        "testcases": [
                            {
                                "name": "example_00",
                                "status": "TLE",
                                "elapsed": 2.47,
                                "memory": 24.08,
                            },
                            {
                                "name": "example_01",
                                "status": "TLE",
                                "elapsed": 2.36,
                                "memory": 24.77,
                            },
                            {
                                "name": "random_00",
                                "status": "TLE",
                                "elapsed": 0.77,
                                "memory": 29.84,
                            },
                            {
                                "name": "random_01",
                                "status": "AC",
                                "elapsed": 6.54,
                                "memory": 11.57,
                            },
                            {
                                "name": "random_02",
                                "status": "AC",
                                "elapsed": 4.54,
                                "memory": 0.66,
                            },
                            {
                                "name": "random_03",
                                "status": "TLE",
                                "elapsed": 8.33,
                                "memory": 30.81,
                            },
                            {
                                "name": "random_04",
                                "status": "AC",
                                "elapsed": 4.31,
                                "memory": 79.42,
                            },
                            {
                                "name": "random_05",
                                "status": "AC",
                                "elapsed": 8.44,
                                "memory": 12.32,
                            },
                            {
                                "name": "random_06",
                                "status": "AC",
                                "elapsed": 6.78,
                                "memory": 26.53,
                            },
                            {
                                "name": "random_07",
                                "status": "TLE",
                                "elapsed": 3.21,
                                "memory": 99.15,
                            },
                            {
                                "name": "random_08",
                                "status": "AC",
                                "elapsed": 3.22,
                                "memory": 55.38,
                            },
                            {
                                "name": "random_09",
                                "status": "TLE",
                                "elapsed": 9.95,
                                "memory": 28.66,
                            },
                        ],
                        "last_execution_time": "2022-03-07T23:17:35.390000+02:00",
                    }
                ],
                "newest": True,
            },
            "targets/python/success1.py": {
                "verifications": [
                    {
                        "verification_name": "Python",
                        "status": "success",
                        "elapsed": 1560.0,
                        "slowest": 156.0,
                        "heaviest": 933.0,
                        "testcases": [
                            {
                                "name": "example_00",
                                "status": "AC",
                                "elapsed": 1.43,
                                "memory": 64.25,
                            },
                            {
                                "name": "example_01",
                                "status": "AC",
                                "elapsed": 9.2,
                                "memory": 70.28,
                            },
                            {
                                "name": "random_00",
                                "status": "AC",
                                "elapsed": 2.39,
                                "memory": 86.29,
                            },
                            {
                                "name": "random_01",
                                "status": "AC",
                                "elapsed": 2.65,
                                "memory": 90.22,
                            },
                            {
                                "name": "random_02",
                                "status": "AC",
                                "elapsed": 1.69,
                                "memory": 5.04,
                            },
                            {
                                "name": "random_03",
                                "status": "AC",
                                "elapsed": 3.85,
                                "memory": 9.68,
                            },
                            {
                                "name": "random_04",
                                "status": "AC",
                                "elapsed": 5.36,
                                "memory": 72.4,
                            },
                            {
                                "name": "random_05",
                                "status": "AC",
                                "elapsed": 4.56,
                                "memory": 66.47,
                            },
                            {
                                "name": "random_06",
                                "status": "AC",
                                "elapsed": 8.28,
                                "memory": 36.75,
                            },
                            {
                                "name": "random_07",
                                "status": "AC",
                                "elapsed": 6.04,
                                "memory": 47.31,
                            },
                            {
                                "name": "random_08",
                                "status": "AC",
                                "elapsed": 7.93,
                                "memory": 35.68,
                            },
                            {
                                "name": "random_09",
                                "status": "AC",
                                "elapsed": 5.7,
                                "memory": 21.75,
                            },
                        ],
                        "last_execution_time": "2038-04-29T10:29:30.730000+11:00",
                    }
                ],
                "newest": True,
            },
            "targets/python/success2.py": {
                "verifications": [
                    {
                        "verification_name": "Python",
                        "status": "success",
                        "elapsed": 5224.0,
                        "slowest": 522.0,
                        "heaviest": 525.0,
                        "testcases": [
                            {
                                "name": "example_00",
                                "status": "AC",
                                "elapsed": 6.73,
                                "memory": 11.63,
                            },
                            {
                                "name": "example_01",
                                "status": "AC",
                                "elapsed": 1.64,
                                "memory": 89.38,
                            },
                            {
                                "name": "random_00",
                                "status": "AC",
                                "elapsed": 6.05,
                                "memory": 66.15,
                            },
                            {
                                "name": "random_01",
                                "status": "AC",
                                "elapsed": 3.86,
                                "memory": 41.39,
                            },
                            {
                                "name": "random_02",
                                "status": "AC",
                                "elapsed": 5.8,
                                "memory": 62.2,
                            },
                            {
                                "name": "random_03",
                                "status": "AC",
                                "elapsed": 3.92,
                                "memory": 99.71,
                            },
                            {
                                "name": "random_04",
                                "status": "AC",
                                "elapsed": 4.85,
                                "memory": 71.44,
                            },
                            {
                                "name": "random_05",
                                "status": "AC",
                                "elapsed": 0.4,
                                "memory": 92.24,
                            },
                            {
                                "name": "random_06",
                                "status": "AC",
                                "elapsed": 4.64,
                                "memory": 21.41,
                            },
                            {
                                "name": "random_07",
                                "status": "AC",
                                "elapsed": 4.51,
                                "memory": 24.87,
                            },
                            {
                                "name": "random_08",
                                "status": "AC",
                                "elapsed": 4.97,
                                "memory": 49.86,
                            },
                            {
                                "name": "random_09",
                                "status": "AC",
                                "elapsed": 0.74,
                                "memory": 77.54,
                            },
                        ],
                        "last_execution_time": "2010-11-21T16:32:46.970000+10:00",
                    }
                ],
                "newest": True,
            },
            "targets/python/failure.re.py": {
                "verifications": [
                    {
                        "verification_name": "Python",
                        "status": "failure",
                        "elapsed": 6846.0,
                        "slowest": 684.0,
                        "heaviest": 84.0,
                        "testcases": [
                            {
                                "name": "example_00",
                                "status": "RE",
                                "elapsed": 9.89,
                                "memory": 58.09,
                            },
                            {
                                "name": "example_01",
                                "status": "RE",
                                "elapsed": 1.1,
                                "memory": 96.01,
                            },
                            {
                                "name": "random_00",
                                "status": "RE",
                                "elapsed": 2.24,
                                "memory": 41.05,
                            },
                            {
                                "name": "random_01",
                                "status": "RE",
                                "elapsed": 9.27,
                                "memory": 38.67,
                            },
                            {
                                "name": "random_02",
                                "status": "RE",
                                "elapsed": 1.62,
                                "memory": 28.54,
                            },
                            {
                                "name": "random_03",
                                "status": "RE",
                                "elapsed": 1.36,
                                "memory": 51.34,
                            },
                            {
                                "name": "random_04",
                                "status": "RE",
                                "elapsed": 2.44,
                                "memory": 26.1,
                            },
                            {
                                "name": "random_05",
                                "status": "RE",
                                "elapsed": 2.89,
                                "memory": 26.67,
                            },
                            {
                                "name": "random_06",
                                "status": "RE",
                                "elapsed": 8.76,
                                "memory": 41.03,
                            },
                            {
                                "name": "random_07",
                                "status": "RE",
                                "elapsed": 0.86,
                                "memory": 29.6,
                            },
                            {
                                "name": "random_08",
                                "status": "RE",
                                "elapsed": 1.56,
                                "memory": 46.89,
                            },
                            {
                                "name": "random_09",
                                "status": "RE",
                                "elapsed": 0.32,
                                "memory": 94.85,
                            },
                        ],
                        "last_execution_time": "2024-07-16T08:47:19.270000-10:00",
                    }
                ],
                "newest": True,
            },
            "targets/python/skip.py": {
                "verifications": [
                    {
                        "status": "skipped",
                        "elapsed": 9827.0,
                        "last_execution_time": "1986-11-01T05:11:16.750000-12:00",
                    }
                ],
                "newest": True,
            },
        },
    }
