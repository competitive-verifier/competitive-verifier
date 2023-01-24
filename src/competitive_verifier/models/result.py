import datetime
import pathlib
from logging import getLogger
from typing import Any, Union

from pydantic import BaseModel, Field, validator

from competitive_verifier.util import to_relative

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
    verifications: list[VerificationResult] = Field(default_factory=list)
    newest: bool = True

    def need_verification(self, base_time: datetime.datetime) -> bool:
        return any(r.need_reverifying(base_time) for r in self.verifications)

    def is_success(self, allow_skip: bool) -> bool:
        if allow_skip:
            return all(r.status != ResultStatus.FAILURE for r in self.verifications)
        else:
            return all(r.status == ResultStatus.SUCCESS for r in self.verifications)


class VerifyCommandResult(BaseModel):
    total_seconds: float
    files: dict[pathlib.Path, FileResult] = Field(default_factory=dict)

    @classmethod
    def parse_file_relative(
        cls, path: Union[str, pathlib.Path], **kwargs: Any
    ) -> "VerifyCommandResult":
        impl = cls.parse_file(path, **kwargs)
        new_files: dict[pathlib.Path, FileResult] = {}
        for p, f in impl.files.items():
            p = to_relative(p)
            if not p:
                continue
            new_files[p] = f

        impl.files = new_files
        return impl

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

    def is_success(self, allow_skip: bool = True) -> bool:
        return all(f.is_success(allow_skip) for f in self.files.values())
