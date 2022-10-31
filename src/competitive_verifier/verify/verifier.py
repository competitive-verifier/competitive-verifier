import datetime
import pathlib

from typing import Optional

from competitive_verifier import github
from competitive_verifier.models.file import VerificationFiles


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
    verification: VerificationFiles
    json_path: pathlib.Path
    use_git_timestamp: bool
    timeout: float
    default_tle: float
    split_state: Optional[SplitState]

    def __init__(
        self,
        verification: VerificationFiles,
        *,
        json_path: pathlib.Path,
        use_git_timestamp: bool,
        timeout: float,
        default_tle: float,
        split_state: Optional[SplitState],
    ) -> None:
        self.verification = verification
        self.json_path = json_path
        self.use_git_timestamp = use_git_timestamp
        self.timeout = timeout
        self.default_tle = default_tle
        self.split_state = split_state

    def get_current_timestamp(self, path: pathlib.Path) -> datetime.datetime:
        dependicies = self.verification.resolve_dependencies(path)
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
