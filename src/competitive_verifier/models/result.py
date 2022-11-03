import datetime
import pathlib
from collections import Counter
from enum import Enum
from logging import getLogger
from typing import Optional, Union

from pydantic import BaseModel

PathLike = Union[str, pathlib.Path]
logger = getLogger(__name__)


class ResultStatus(str, Enum):
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    SKIPPED = "SKIPPED"


class FileVerificationResult(BaseModel):
    path: pathlib.Path
    command_result: ResultStatus
    last_success_time: Optional[datetime.datetime] = None

    class Config:
        use_enum_values = True

    def is_updated(self, base_time: datetime.datetime) -> bool:
        return (
            self.last_success_time is not None and self.last_success_time >= base_time
        )


class VerificationResult(BaseModel):
    files: list[FileVerificationResult]

    def show_summary(self) -> None:
        counter = Counter(r.command_result for r in self.files)
        logger.info(
            " ".join(f"Test result: {s.value}: {counter.get(s)}" for s in ResultStatus)
        )
