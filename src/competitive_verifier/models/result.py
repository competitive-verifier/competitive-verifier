import datetime
import pathlib
from logging import getLogger
from typing import Optional

logger = getLogger(__name__)


class FileVerificationResult:
    path: pathlib.Path
    last_verifid_time: Optional[datetime.datetime]
    last_success_time: Optional[datetime.datetime]

    def __init__(
        self,
        path: pathlib.Path,
        *,
        last_verifid_time: Optional[datetime.datetime],
        last_success_time: Optional[datetime.datetime],
    ):
        self.path = path
        self.last_verifid_time = last_verifid_time
        self.last_success_time = last_success_time

    def is_success(self) -> bool:
        return (
            self.last_success_time is not None
            and self.last_success_time == self.last_verifid_time
        )


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
