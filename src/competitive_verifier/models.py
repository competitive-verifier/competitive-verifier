import pathlib
from enum import Enum
from logging import getLogger
from typing import Any, Optional

import competitive_verifier.command
from competitive_verifier.command import VerificationCommand

logger = getLogger(__name__)


class VerificationFile:
    def __init__(
        self,
        path: pathlib.Path,
        *,
        dependencies: list[pathlib.Path],
        verification: Optional[VerificationCommand],
    ):
        self.path = path
        self.dependencies = dependencies
        self.verification = verification


class VerificationFiles:
    def __init__(self, *, files: list[VerificationFile]):
        self.files = files


def decode_verification_files(d: dict[Any, Any]) -> VerificationFiles:
    def decode_verification(
        d: Optional[dict[Any, Any]]
    ) -> Optional[VerificationCommand]:
        return competitive_verifier.command.decode(d) if d else None

    return VerificationFiles(
        files=[
            VerificationFile(
                f["path"],
                dependencies=f["dependencies"],
                verification=decode_verification(f.get("verification")),
            )
            for f in d["files"]
        ]
    )


class VerificationResultStatus(Enum):
    SUCCESS = 1
    FAILURE = 2


class FileVerificationResult:
    def __init__(self, path: pathlib.Path, status: VerificationResultStatus):
        self.path = path
        self.status = status

    def is_success(self) -> bool:
        return self.status == VerificationResultStatus.SUCCESS


class VerificationResult:
    def __init__(self, *, file_results: list[FileVerificationResult]):
        self.file_results = file_results

    def show_summary(self) -> None:
        failed_results = [r for r in self.file_results if not r.is_success()]
        if failed_results:
            logger.error(f"{len(failed_results)} tests failed")
            for r in failed_results:
                logger.error(
                    "failed: %s", str(r.path.resolve().relative_to(pathlib.Path.cwd()))
                )
        else:
            logger.info("all tests succeeded")

    def is_success(self) -> bool:
        return all(r.is_success() for r in self.file_results)
