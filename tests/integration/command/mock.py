import datetime
import pathlib
import shutil
import subprocess
import sys
import tarfile
from typing import Any, Literal

import requests

from competitive_verifier import config
from competitive_verifier.models import FileResult, VerificationResult
from competitive_verifier.models import TestcaseResult as _TestcaseResult
from competitive_verifier.verify import verifier

from .utils import md5_number


class MockVerifyCommandResult(verifier.VerifyCommandResult):
    def model_dump_json(  # type: ignore[override]
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
        warnings: bool | Literal["none", "warn", "error"] = True,
    ) -> str:  # pragma: no cover
        return self.model_copy()._dump_super(  # noqa: SLF001
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
        warnings: bool | Literal["none", "warn", "error"] = True,
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
            seed += case.name.encode()
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


_library_checker_problems_tar_gz: bytes | None = None


def update_cloned_repository():  # pragma: no cover
    global _library_checker_problems_tar_gz  # noqa: PLW0603

    gz_path = config.get_cache_dir() / "library-checker-problems.tar.gz"
    repo_gz_path = config.get_cache_dir() / "repo.tar.gz"
    repo_path = config.get_cache_dir() / "library-checker-problems"
    if repo_path.is_dir():
        return

    if not gz_path.exists() and _library_checker_problems_tar_gz:
        gz_path.write_bytes(_library_checker_problems_tar_gz)
    if gz_path.exists():
        shutil.unpack_archive(gz_path, config.get_cache_dir())
        return

    config.get_cache_dir().mkdir(parents=True, exist_ok=True)
    res = requests.get(
        "https://github.com/yosupo06/library-checker-problems/archive/refs/heads/master.tar.gz",
        timeout=60,
    )

    repo_gz_path.write_bytes(res.content)
    shutil.unpack_archive(repo_gz_path, config.get_cache_dir())
    repo_gz_path.unlink(missing_ok=True)

    master_dir = config.get_cache_dir() / "library-checker-problems-master"

    gen_cmd = [sys.executable, "generate.py", "sample/aplusb/info.toml"]
    subprocess.check_call(gen_cmd, cwd=master_dir, timeout=60)

    with tarfile.open(gz_path, "w:gz") as gzp:
        gzp.add(master_dir, "library-checker-problems", filter=_match_aplusb)
    _library_checker_problems_tar_gz = gz_path.read_bytes()

    shutil.move(master_dir, repo_path)


def _match_aplusb(t: tarfile.TarInfo) -> tarfile.TarInfo | None:
    if (
        t.path.startswith("library-checker-problems/sample/aplusb")
        or (t.isdir() and "library-checker-problems/sample/aplusb".startswith(t.path))
        or t.isfile()
    ):
        return t
    return None
