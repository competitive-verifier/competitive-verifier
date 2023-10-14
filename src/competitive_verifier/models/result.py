import datetime
import pathlib
from logging import getLogger
from typing import Any, Optional, Union

from onlinejudge_command.subcommand.test import JudgeStatus
from pydantic import BaseModel, Field, field_validator

from competitive_verifier.models.path import ForcePosixPath
from competitive_verifier.util import to_relative

from .result_status import ResultStatus

logger = getLogger(__name__)


class TestcaseResult(BaseModel):
    name: str
    status: JudgeStatus
    elapsed: float
    memory: Optional[float]


class VerificationResult(BaseModel):
    verification_name: Optional[str] = None
    status: ResultStatus
    elapsed: float
    """
    Elapsed seconds
    """
    slowest: Optional[float] = None
    """
    slowest seconds
    """
    heaviest: Optional[float] = None
    """
    heaviest MB
    """

    testcases: Optional[list[TestcaseResult]] = None

    last_execution_time: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc)
    )

    @field_validator("status", mode="before")
    @classmethod
    def verification_list(cls, v: Any) -> Any:
        if isinstance(v, str):
            return v.lower()
        return v

    def need_reverifying(self, base_time: datetime.datetime) -> bool:
        if self.status != ResultStatus.SUCCESS:
            return True

        return self.last_execution_time < base_time


class FileResult(BaseModel):
    verifications: list[VerificationResult] = Field(default_factory=list)
    newest: bool = True

    def need_verification(self, base_time: datetime.datetime) -> bool:
        if len(self.verifications) == 0:
            return True
        return any(r.need_reverifying(base_time) for r in self.verifications)

    def is_success(self, allow_skip: bool) -> bool:
        if allow_skip:
            return all(r.status != ResultStatus.FAILURE for r in self.verifications)
        else:
            return all(r.status == ResultStatus.SUCCESS for r in self.verifications)


class VerifyCommandResult(BaseModel):
    total_seconds: float
    files: dict[ForcePosixPath, FileResult] = Field(default_factory=dict)

    @classmethod
    def parse_file_relative(
        cls, path: Union[str, pathlib.Path], **kwargs: Any
    ) -> "VerifyCommandResult":
        with pathlib.Path(path).open("rb") as p:
            impl = cls.model_validate_json(p.read(), **kwargs)
        new_files: dict[pathlib.Path, FileResult] = {}
        for p, f in impl.files.items():
            p = to_relative(p)
            if not p:
                continue
            new_files[p] = f

        impl.files = new_files
        return impl

    def merge(self, other: "VerifyCommandResult") -> "VerifyCommandResult":
        d = self.files.copy()
        for k, r in other.files.items():
            cur = d.get(k)
            if r.newest or (cur is None) or (not cur.newest):
                d[k] = r
        return VerifyCommandResult(
            total_seconds=self.total_seconds + other.total_seconds,
            files=d,
        )

    def is_success(self, allow_skip: bool = True) -> bool:
        return all(f.is_success(allow_skip) for f in self.files.values())
