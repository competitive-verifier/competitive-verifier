import datetime
import pathlib
from collections import Counter
from enum import Enum
from logging import getLogger
from typing import Any, Optional, Union

PathLike = Union[str, pathlib.Path]
logger = getLogger(__name__)


class ResultStatus(str, Enum):
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    SKIPPED = "SKIPPED"


class FileVerificationResult:
    path: pathlib.Path
    command_result: ResultStatus
    last_success_time: Optional[datetime.datetime]

    def __init__(
        self,
        path: PathLike,
        *,
        command_result: ResultStatus,
        last_success_time: Optional[datetime.datetime] = None,
    ):
        self.path = pathlib.Path(path)
        self.command_result = command_result
        self.last_success_time = last_success_time

    def is_updated(self, base_time: datetime.datetime) -> bool:
        return (
            self.last_success_time is not None and self.last_success_time >= base_time
        )


class VerificationResult:
    def __init__(self, *, files: list[FileVerificationResult]):
        self.files = files

    def show_summary(self, start_time: datetime.datetime) -> None:
        counter = Counter(r.command_result for r in self.files)
        logger.info(
            " ".join(f"Test result: {s.value}: {counter.get(s)}" for s in ResultStatus)
        )


def decode_result_json(d: dict[Any, Any]) -> VerificationResult:
    def decode_datetime(s: Optional[str]) -> Optional[datetime.datetime]:
        if s is None:
            return None
        return datetime.datetime.strptime(s, "%Y-%m-%d %H:%M:%S %z")

    def decode_file_result(d: dict[Any, Any]) -> FileVerificationResult:
        return FileVerificationResult(
            path=d["path"],
            command_result=ResultStatus(d["command_result"]),
            last_success_time=decode_datetime(d.get("last_success_time")),
        )

    return VerificationResult(files=[decode_file_result(x) for x in d["results"]])
