import datetime
import json
import pathlib
from logging import getLogger
from typing import Any, Optional, TextIO

logger = getLogger(__name__)


class FileVerificationResult:
    path: pathlib.Path
    last_verifid_time: Optional[datetime.datetime]
    last_success_time: Optional[datetime.datetime]

    def __init__(
        self,
        path: pathlib.Path,
        *,
        last_verifid_time: Optional[datetime.datetime] = None,
        last_success_time: Optional[datetime.datetime] = None,
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
    def __init__(self, *, results: list[FileVerificationResult]):
        self.results = results

    def show_summary(self) -> None:
        failed_results = [r for r in self.results if not r.is_success()]
        if failed_results:
            logger.error(f"{len(failed_results)} tests failed")
            for r in failed_results:
                logger.error(
                    "failed: %s", str(r.path.resolve().relative_to(pathlib.Path.cwd()))
                )
        else:
            logger.info("all tests succeeded")

    def is_success(self) -> bool:
        return all(r.is_success() for r in self.results)


def decode_result_json(d: dict[Any, Any]) -> VerificationResult:
    return VerificationResult(
        results=[FileVerificationResult(**x) for x in d["results"]]
    )
