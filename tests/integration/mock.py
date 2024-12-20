import datetime
import pathlib
import shutil
import subprocess
import sys
import tarfile
from typing import Any, Literal, Optional, Union

import requests

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
        context: Any = None,
        warnings: Union[bool, Literal["none", "warn", "error"]] = True,
        serialize_as_any: bool = False,
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
        warnings: Union[bool, Literal["none", "warn", "error"]] = True,
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


_library_checker_problems_tar_gz: Optional[bytes] = None


def update_cloned_repository() -> None:
    global _library_checker_problems_tar_gz

    gz_path = config.get_cache_dir() / "library-checker-problems.tar.gz"
    gz_path = gz_path.resolve()
    if not gz_path.exists():
        gz_path.parent.mkdir(parents=True, exist_ok=True)

        if _library_checker_problems_tar_gz:
            gz_path.write_bytes(_library_checker_problems_tar_gz)
            shutil.unpack_archive(gz_path, config.get_cache_dir())
        else:
            res = requests.get(
                "https://github.com/yosupo06/library-checker-problems/archive/refs/heads/master.tar.gz"
            )
            content = res.content

            with gz_path.open("wb") as fp:
                fp.write(content)

            shutil.unpack_archive(gz_path, config.get_cache_dir())
            master_dir = config.get_cache_dir() / "library-checker-problems-master"

            subprocess.check_call(
                [sys.executable, "generate.py", "sample/aplusb/info.toml"],
                cwd=master_dir,
            )

            gz_path.unlink(missing_ok=True)
            with tarfile.open(gz_path, "w:gz") as gzp:
                gzp.add(master_dir, "library-checker-problems", filter=_match_aplusb)
            _library_checker_problems_tar_gz = gz_path.read_bytes()

            shutil.move(
                master_dir,
                config.get_cache_dir() / "library-checker-problems",
            )


def _match_aplusb(t: tarfile.TarInfo) -> Optional[tarfile.TarInfo]:
    if t.isdir():
        if "library-checker-problems/sample/aplusb".startswith(t.path):
            return t
        elif t.path.startswith("library-checker-problems/sample/aplusb"):
            return t
    elif t.isfile():
        if t.path.startswith("library-checker-problems/sample/aplusb"):
            return t
        elif t.path.endswith(".py"):
            return t
    return None
