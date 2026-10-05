import datetime
import enum
import pathlib
from logging import getLogger
from typing import TYPE_CHECKING, Any, overload

from pydantic import BaseModel, Field, field_validator

from competitive_verifier.log import GitHubMessageParams
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

    memory: float | None = Field(
        default=None,
        description="The size of memory used in megabytes.",
    )
    """The size of memory used in megabytes.
    """


class VerificationResult(BaseModel):
    verification_name: str | None = Field(
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

    slowest: float | None = Field(
        default=None,
        description="Maximum number of seconds elapsed for each test cases.",
    )
    """Maximum number of seconds elapsed for each test cases.
    """

    heaviest: float | None = Field(
        default=None,
        description="Maximum size of memory used in megabytes.",
    )
    """Maximum size of memory used in megabytes.
    """

    testcases: list[TestcaseResult] | None = Field(
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
    def verification_list(cls, v: Any) -> Any:  # noqa: ANN401
        return v.lower() if isinstance(v, str) else v

    def need_reverifying(self, base_time: datetime.datetime) -> bool:
        if self.status != ResultStatus.SUCCESS:
            return True

        return self.last_execution_time < base_time


class NeedVerification(enum.Enum):
    """Why a previous ``FileResult`` can't be reused; falsy when it can."""

    NO = "unchanged since the previous verification"
    NO_RESULT = "no previous result"
    NOT_SUCCESS = "the previous verification didn't succeed"
    MODIFIED = "modified after the previous verification"
    NO_CONTENT_HASH = "the previous result has no content hash"
    CONTENT_CHANGED = "content hash changed"
    NO_TESTDATA_HASH = "the previous result has no test data hash"
    TESTDATA_CHANGED = "test data hash changed"

    def __bool__(self) -> bool:
        return self is not NeedVerification.NO


class FileResult(BaseModel):
    verifications: list[VerificationResult] = Field(
        default_factory=list[VerificationResult],
        description="The results of each verification.",
    )
    """The results of each verification.
    """

    content_hash: str | None = Field(
        default=None,
        description="Digest of the file and its transitive dependencies"
        " at verification time.",
    )
    """Digest of the file and its transitive dependencies at verification time.
    """

    testdata_hash: str | None = Field(
        default=None,
        description="Digest of the test data used by the verifications,"
        " or null if it is never expected to change or isn't downloaded yet.",
    )
    """Digest of the test data used by the verifications,
    or null if it is never expected to change or isn't downloaded yet.
    """

    newest: bool = Field(
        default=True,
        description="Whether the verification was performed on the most recent run.",
    )
    """Whether the verification was performed on the most recent run.
    """

    @overload
    def need_verification(
        self,
        *,
        base_time: datetime.datetime,
        testdata_hash: str | None = None,
    ) -> NeedVerification: ...

    @overload
    def need_verification(
        self,
        *,
        content_hash: str | None,
        testdata_hash: str | None,
    ) -> NeedVerification: ...

    def need_verification(
        self,
        *,
        base_time: datetime.datetime | None = None,
        content_hash: str | None = None,
        testdata_hash: str | None = None,
    ) -> NeedVerification:
        """Whether the file or its test data has changed since this result.

        Pass ``base_time`` to compare against the file's modification time,
        or ``content_hash`` (and ``testdata_hash``, when the test data can be
        identified) to compare against the recorded hashes.
        """
        if len(self.verifications) == 0:
            return NeedVerification.NO_RESULT
        if base_time is not None:
            return self._need_verification_by_time(base_time)
        return self._need_verification_by_hash(content_hash, testdata_hash)

    def _need_verification_by_time(
        self, base_time: datetime.datetime
    ) -> NeedVerification:
        if any(r.status != ResultStatus.SUCCESS for r in self.verifications):
            return NeedVerification.NOT_SUCCESS
        if any(r.last_execution_time < base_time for r in self.verifications):
            return NeedVerification.MODIFIED
        return NeedVerification.NO

    def _need_verification_by_hash(
        self, content_hash: str | None, testdata_hash: str | None
    ) -> NeedVerification:
        if self.content_hash is None:
            return NeedVerification.NO_CONTENT_HASH
        if self.content_hash != content_hash:
            return NeedVerification.CONTENT_CHANGED
        if testdata_hash is not None:
            if self.testdata_hash is None:
                return NeedVerification.NO_TESTDATA_HASH
            if self.testdata_hash != testdata_hash:
                return NeedVerification.TESTDATA_CHANGED
        if not self.is_success(allow_skip=False):
            return NeedVerification.NOT_SUCCESS
        return NeedVerification.NO

    def is_success(self, *, allow_skip: bool) -> bool:
        if allow_skip:
            return all(r.status != ResultStatus.FAILURE for r in self.verifications)
        return all(r.status == ResultStatus.SUCCESS for r in self.verifications)


class VerifyCommandResult(BaseModel):
    total_seconds: float = Field(
        description="Total number of seconds elapsed for all verification.",
    )
    """Total number of seconds elapsed for all verification.
    """

    files: dict[ForcePosixPath, FileResult] = Field(
        default_factory=dict[ForcePosixPath, FileResult],
        description="The files to be verified.",
    )
    """The files to be verified.
    """

    @classmethod
    def parse_file_relative(cls, path: "StrPath") -> "VerifyCommandResult":
        impl = cls.model_validate_json(pathlib.Path(path).read_bytes())
        new_files: dict[pathlib.Path, FileResult] = {}
        for p, f in impl.files.items():
            rp = to_relative(p)
            if not rp:
                logger.warning(
                    "Files in other directories are not subject to verification: %s",
                    p,
                    extra={"github": GitHubMessageParams()},
                )
                continue
            new_files[rp] = f

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

    def is_success(self, *, allow_skip: bool = True) -> bool:
        return all(f.is_success(allow_skip=allow_skip) for f in self.files.values())
