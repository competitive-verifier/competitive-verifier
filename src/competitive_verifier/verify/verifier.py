import datetime
import pathlib
from functools import cached_property
from typing import Optional

from competitive_verifier import github
from competitive_verifier.models.file import VerificationFile, VerificationFiles
from competitive_verifier.models.result import VerificationResult
from competitive_verifier.verify.util import VerifyError


class SplitState:
    size: int
    index: int

    def __init__(
        self,
        *,
        size: int,
        index: int,
    ) -> None:
        self.size = size
        self.index = index

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SplitState):
            return NotImplemented
        return self.size == other.size and self.index == other.index


class Verifier:
    files: VerificationFiles

    use_git_timestamp: bool
    timeout: float
    default_tle: float
    prev_result: Optional[VerificationResult]
    split_state: Optional[SplitState]

    result: Optional[VerificationResult]
    verification_time: datetime.datetime

    def __init__(
        self,
        files: VerificationFiles,
        *,
        use_git_timestamp: bool,
        timeout: float,
        default_tle: float,
        prev_result: Optional[VerificationResult],
        split_state: Optional[SplitState],
        verification_time: Optional[datetime.datetime] = None,
    ) -> None:
        self.files = files
        self.prev_result = prev_result
        self.use_git_timestamp = use_git_timestamp
        self.timeout = timeout
        self.default_tle = default_tle
        self.split_state = split_state
        self.verification_time = verification_time or datetime.datetime.now()
        self.result = None

    @property
    def force_result(self) -> VerificationResult:
        if self.result is None:
            raise VerifyError("Not verified yet.")
        return self.result

    def is_success(self) -> bool:
        if self.result is None:
            return False
        for res in self.result.results:
            if not res.is_success(
                min(self.verification_time, self.get_current_timestamp(res.path))
            ):
                return False
        return True

    def get_current_timestamp(self, path: pathlib.Path) -> datetime.datetime:
        dependicies = self.files.resolve_dependencies(path)
        if self.use_git_timestamp:
            return github.get_commit_time(dependicies)
        else:
            timestamp = max(x.stat().st_mtime for x in dependicies)
            system_local_timezone = (
                datetime.datetime.now(datetime.timezone.utc).astimezone().tzinfo
            )
            return datetime.datetime.fromtimestamp(
                timestamp, tz=system_local_timezone
            ).replace(
                microsecond=0
            )  # microsecond=0 is required because it's erased in git commit

    @cached_property
    def verification_files(self) -> list[VerificationFile]:
        return [f for f in self.files.files if f.verification is not None]
