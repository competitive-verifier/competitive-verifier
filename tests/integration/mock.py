import datetime
import pathlib
import shutil
from typing import Any, Iterable, List

import onlinejudge.service.library_checker as library_checker
import requests
from onlinejudge.type import TestCase as OjTestCase

import competitive_verifier.config as config
from competitive_verifier.models import FileResult
from competitive_verifier.models import TestcaseResult as _TestcaseResult
from competitive_verifier.models import VerificationResult
from competitive_verifier.verify import verifier
from tests.integration.utils import md5_number


class MockVerifyCommandResult(verifier.VerifyCommandResult):
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


class MockLibraryCheckerProblem(library_checker.LibraryCheckerProblem):
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

    def _mock_cases(self) -> Iterable[OjTestCase]:
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
