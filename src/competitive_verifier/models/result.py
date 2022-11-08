import datetime
import pathlib
from logging import getLogger
from typing import Any

from pydantic import BaseModel, Field, validator

from .result_status import ResultStatus

logger = getLogger(__name__)


class VerificationResult(BaseModel):
    status: ResultStatus
    elapsed: float
    """
    Elapsed seconds
    """

    last_execution_time: datetime.datetime = Field(
        default_factory=datetime.datetime.now
    )

    @validator("status", pre=True)
    def verification_list(cls, v: Any) -> Any:
        if isinstance(v, str):
            return v.lower()
        return v

    def need_reverifying(self, base_time: datetime.datetime) -> bool:
        if self.status != ResultStatus.SUCCESS:
            return True
        if self.last_execution_time is None:
            return True

        return self.last_execution_time < base_time


class FileResult(BaseModel):
    command_results: list[VerificationResult] = Field(default_factory=list)
    newest: bool = True

    def need_verification(self, base_time: datetime.datetime) -> bool:
        return any(r.need_reverifying(base_time) for r in self.command_results)

    def is_success(self) -> bool:
        return all(r.status == ResultStatus.SUCCESS for r in self.command_results)


class VerifyCommandResult(BaseModel):
    total_seconds: float
    files: dict[pathlib.Path, FileResult] = Field(default_factory=dict)

    def json(self, **kwargs: Any) -> str:
        class WithStrDict(BaseModel):
            total_seconds: float
            files: dict[str, FileResult]

            class Config:
                json_encoders = {pathlib.Path: lambda v: v.as_posix()}  # type: ignore

        return WithStrDict(
            total_seconds=self.total_seconds,
            files={k.as_posix(): v for k, v in self.files.items()},
        ).json(**kwargs)

    def merge(self, other: "VerifyCommandResult") -> "VerifyCommandResult":
        d = self.files.copy()
        d.update(other.files)
        return VerifyCommandResult(
            total_seconds=self.total_seconds + other.total_seconds,
            files=d,
        )

    def is_success(self) -> bool:
        return all(f.is_success() for f in self.files.values())

    # def show_summary(self) -> None:
    #     counter = Counter(r.command_result for r in self.files)
    #     logger.info(
    #         " ".join(f"Test result: {s.value}: {counter.get(s)}"
    #          for s in ResultStatus)
    #     )
