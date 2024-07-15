import datetime
import pathlib
from logging import getLogger
from typing import TYPE_CHECKING, Any, Optional

from pydantic import BaseModel, Field, field_validator

from competitive_verifier.util import to_relative

from .path import ForcePosixPath
from .result_status import JudgeStatus, ResultStatus

if TYPE_CHECKING:
    from _typeshed import StrPath

logger = getLogger(__name__)


class TestcaseResult(BaseModel):
    name: str = Field(
        description="The name of test case.",
    )
    """The name of test case.
    """

    status: JudgeStatus = Field(
        description="The result status of the test case.",
    )
    """The result status of the test case.
    """

    elapsed: float = Field(
        description="Number of seconds elapsed for the test case.",
    )
    """Number of seconds elapsed for the test case.
    """

    memory: Optional[float] = Field(
        default=None,
        description="The size of memory used in megabytes.",
    )
    """The size of memory used in megabytes.
    """


class VerificationResult(BaseModel):
    verification_name: Optional[str] = Field(
        default=None,
        description="The name of verification.",
    )
    """The name of verification.
    """
    status: ResultStatus = Field(
        description="The result status of verification.",
    )
    """The result status of verification.
    """

    elapsed: float = Field(
        description="Total number of seconds elapsed for all test cases.",
    )
    """Total number of seconds elapsed for all test cases.
    """

    slowest: Optional[float] = Field(
        default=None,
        description="Maximum number of seconds elapsed for each test cases.",
    )
    """Maximum number of seconds elapsed for each test cases.
    """

    heaviest: Optional[float] = Field(
        default=None,
        description="Maximum size of memory used in megabytes.",
    )
    """Maximum size of memory used in megabytes.
    """

    testcases: Optional[list[TestcaseResult]] = Field(
        default=None,
        description="The results of each test case.",
    )
    """The results of each test case.
    """

    last_execution_time: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc),
        description="The time at which the last validation was performed.",
    )
    """The time at which the last validation was performed.
    """

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
    verifications: list[VerificationResult] = Field(
        default_factory=list,
        description="The results of each verification.",
    )
    """The results of each verification.
    """

    newest: bool = Field(
        default=True,
        description="Whether the verification was performed on the most recent run.",
    )
    """Whether the verification was performed on the most recent run.
    """

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
    total_seconds: float = Field(
        description="Total number of seconds elapsed for all verification.",
    )
    """Total number of seconds elapsed for all verification.
    """

    files: dict[ForcePosixPath, FileResult] = Field(
        default_factory=dict,
        description="The files to be verified.",
    )
    """The files to be verified.
    """

    @classmethod
    def parse_file_relative(
        cls, path: "StrPath", **kwargs: Any
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
