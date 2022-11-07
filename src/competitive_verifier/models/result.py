import datetime
import pathlib
from enum import Enum
from logging import getLogger
from typing import Any

from pydantic import BaseModel, Field

logger = getLogger(__name__)


class ResultStatus(str, Enum):
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    SKIPPED = "SKIPPED"


class CommandResult(BaseModel):
    status: ResultStatus
    last_execution_time: datetime.datetime = Field(
        default_factory=datetime.datetime.now
    )

    class Config:
        use_enum_values = True

    def need_reverifying(self, base_time: datetime.datetime) -> bool:
        if self.status != ResultStatus.SUCCESS:
            return True
        if self.last_execution_time is None:
            return True

        return self.last_execution_time < base_time


class FileResult(BaseModel):
    command_results: list[CommandResult] = Field(default_factory=list)

    def need_verification(self, base_time: datetime.datetime) -> bool:
        return any(r.need_reverifying(base_time) for r in self.command_results)

    def is_success(self) -> bool:
        return all(r.status == ResultStatus.SUCCESS for r in self.command_results)


class VerificationResult(BaseModel):
    files: dict[pathlib.Path, FileResult] = Field(default_factory=dict)

    def json(self, **kwargs: Any) -> str:
        class WithStrDict(BaseModel):
            files: dict[str, FileResult]

            class Config:
                json_encoders = {pathlib.Path: lambda v: v.as_posix()}  # type: ignore

        return WithStrDict(
            files={k.as_posix(): v for k, v in self.files.items()},
        ).json(**kwargs)

    def merge(self, other: "VerificationResult") -> "VerificationResult":
        d = self.files.copy()
        d.update(other.files)
        return VerificationResult(files=d)

    def is_success(self) -> bool:
        return all(f.is_success() for f in self.files.values())

    # def show_summary(self) -> None:
    #     counter = Counter(r.command_result for r in self.files)
    #     logger.info(
    #         " ".join(f"Test result: {s.value}: {counter.get(s)}"
    #          for s in ResultStatus)
    #     )
