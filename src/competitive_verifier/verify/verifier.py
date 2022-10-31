import datetime
import pathlib
from functools import cached_property
from logging import getLogger
import subprocess
import textwrap
from typing import Optional, TypeVar

from competitive_verifier import github
from competitive_verifier.models.file import VerificationFile, VerificationInput
from competitive_verifier.models.result import (
    FileVerificationResult,
    VerificationResult,
)
from competitive_verifier.error import VerifierError
from competitive_verifier.verify.resource import ulimit_stack

logger = getLogger(__name__)
T = TypeVar("T")


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

    def __repr__(self) -> str:
        return f"SplitState(size={self.size}, index={self.index})"

    def __str__(self) -> str:
        return f"{self.index}/{self.size}"

    def split(self, lst: list[T]) -> list[T]:
        """Split list


        Args:
            lst (list[T]): Target list

        Returns:
            list[T]: Splited list

        Example:
            state = SplitState(size=3, index=0)
            assert state.split([0, 1, 2, 3, 4]) == [0]
            state = SplitState(size=3, index=1)
            assert state.split([0, 1, 2, 3, 4]) == [1, 2]
            state = SplitState(size=3, index=2)
            assert state.split([0, 1, 2, 3, 4]) == [3, 4]
            state = SplitState(size=6, index=4)
            assert state.split([0, 1, 2, 3, 4]) == [4]
            state = SplitState(size=6, index=5)
            assert state.split([0, 1, 2, 3, 4]) == []
        """

        if len(lst) <= self.size:
            if len(lst) <= self.index:
                return []
            else:
                return [lst[self.index]]

        from_index = len(lst) * self.index // self.size
        to_index = len(lst) * (self.index + 1) // self.size
        return lst[from_index:to_index]


class Verifier:
    input: VerificationInput

    use_git_timestamp: bool
    timeout: float
    default_tle: float
    prev_result: Optional[VerificationResult]
    split_state: Optional[SplitState]

    _result: Optional[VerificationResult]
    verification_time: datetime.datetime

    def __init__(
        self,
        input: VerificationInput,
        *,
        use_git_timestamp: bool,
        timeout: float,
        default_tle: float,
        prev_result: Optional[VerificationResult],
        split_state: Optional[SplitState],
        verification_time: Optional[datetime.datetime] = None,
    ) -> None:
        self.input = input
        self.prev_result = prev_result
        self.use_git_timestamp = use_git_timestamp
        self.timeout = timeout
        self.default_tle = default_tle
        self.split_state = split_state
        self.verification_time = verification_time or datetime.datetime.now()
        self._result = None

    @property
    def force_result(self) -> VerificationResult:
        if self._result is None:
            raise VerifierError("Not verified yet.")
        return self._result

    def is_success_file(self, file_result: FileVerificationResult) -> bool:
        return file_result.is_success(
            min(self.verification_time, self.get_current_timestamp(file_result.path))
        )

    def is_success(self) -> bool:
        if self._result is None:
            return False
        for fr in self._result.files:
            if not self.is_success_file(fr):
                return False
        return True

    def get_current_timestamp(self, path: pathlib.Path) -> datetime.datetime:
        dependicies = self.input.resolve_dependencies(path)
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
        """
        List of verification files.
        """
        res = [f for f in self.input.files if f.is_verification]
        res.sort(key=lambda f: str(f.path))
        return res

    @cached_property
    def remaining_verification_files(self) -> list[VerificationFile]:
        """
        List of verification files that have not yet been verified.
        """
        verification_files = self.verification_files

        if self.prev_result is None:
            return verification_files

        succeeded_files = set(
            r.path for r in self.prev_result.files if self.is_success_file(r)
        )
        return [f for f in verification_files if f.path not in succeeded_files]

    @cached_property
    def current_verification_files(self) -> list[VerificationFile]:
        """
        List of verification files that self should verify.

        if ``split_state`` is None the property is ``remaining_verification_files``;

        else ``split_state.split(remaining_verification_files)``.
        """
        if self.split_state is None:
            return self.remaining_verification_files

        return self.split_state.split(self.remaining_verification_files)

    def verify(self) -> VerificationResult:
        logger.info(
            "current_verification_files=%s",
            [str(f.path) for f in self.current_verification_files],
        )
        try:
            ulimit_stack()
        except Exception:
            logger.warning("failed to increase the stack size[ulimit]")

        compile_command = self.input.compile_command
        if compile_command:
            try:
                compile_result = subprocess.run(
                    self.input.compile_command,
                    capture_output=True,
                    text=True,
                    check=True,
                )
                logger.info(compile_result)
            except (subprocess.CalledProcessError) as e:
                logger.error("Failed to compile: %s", compile_command)
                stdout: str = e.stdout  # type: ignore
                stderr: str = e.stderr  # type: ignore
                raise VerifierError(
                    textwrap.dedent(
                        f"""\
                        Failed to compile

                        stdout:
                            {stdout}

                        stderr:
                            {stderr}
                        """
                    ),
                    inner=e,
                )
            except (FileNotFoundError) as e:
                logger.error("Failed to compile: %s", compile_command)
                raise VerifierError(
                    textwrap.dedent(
                        """\
                        The command is not found
                        """
                    ),
                    inner=e,
                )
        else:
            logger.debug("There is no complie command")

        # TODO: Finish
        return VerificationResult(files=[])
