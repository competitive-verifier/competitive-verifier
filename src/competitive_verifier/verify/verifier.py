import datetime
import pathlib
import traceback
from abc import ABC, abstractmethod
from functools import cached_property
from logging import getLogger
from typing import Optional

from competitive_verifier import github, log
from competitive_verifier.download.main import run_impl as run_download
from competitive_verifier.error import VerifierError
from competitive_verifier.models import (
    FileResult,
    ResultStatus,
    VerificationFile,
    VerificationInput,
    VerificationResult,
    VerifyCommandResult,
)
from competitive_verifier.verify.resource import ulimit_stack
from competitive_verifier.verify.split_state import SplitState

logger = getLogger(__name__)


class InputContainer(ABC):
    input: VerificationInput
    verification_time: datetime.datetime
    prev_result: Optional[VerifyCommandResult]
    split_state: Optional[SplitState]

    def __init__(
        self,
        *,
        input: VerificationInput,
        verification_time: datetime.datetime,
        prev_result: Optional[VerifyCommandResult],
        split_state: Optional[SplitState],
    ) -> None:
        self.input = input
        self.verification_time = verification_time
        self.prev_result = prev_result
        self.split_state = split_state

    @abstractmethod
    def get_file_timestamp(self, path: pathlib.Path) -> datetime.datetime:
        ...

    def file_need_verification(
        self,
        path: pathlib.Path,
        file_result: FileResult,
    ) -> bool:
        return file_result.need_verification(
            min(self.verification_time, self.get_file_timestamp(path))
        )

    @cached_property
    def verification_files(self) -> dict[pathlib.Path, VerificationFile]:
        """
        List of verification files.
        """
        return {p: f for p, f in self.input.files.items() if f.is_verification()}

    @cached_property
    def remaining_verification_files(self) -> dict[pathlib.Path, VerificationFile]:
        """
        List of verification files that have not yet been verified.
        """
        verification_files = {
            p: f
            for p, f in self.verification_files.items()
            if not f.is_skippable_verification()
        }

        if self.prev_result is None:
            return verification_files

        not_updated_files = set(
            p
            for p, r in self.prev_result.files.items()
            if not self.file_need_verification(p, r)
        )
        verification_files = {
            p: f for p, f in verification_files.items() if p not in not_updated_files
        }
        return verification_files

    @cached_property
    def current_verification_files(self) -> dict[pathlib.Path, VerificationFile]:
        """
        List of verification files that self should verify.

        if ``split_state`` is None the property is ``remaining_verification_files``;

        else ``split_state.split(remaining_verification_files)``.
        """
        if self.split_state is None:
            return self.remaining_verification_files

        lst = [(p, f) for p, f in self.remaining_verification_files.items()]
        lst.sort(key=lambda tup: tup[0])
        return {p: f for p, f in self.split_state.split(lst)}


class Verifier(InputContainer):
    use_git_timestamp: bool
    timeout: float
    default_tle: float
    split_state: Optional[SplitState]

    _result: Optional[VerifyCommandResult]

    def __init__(
        self,
        input: VerificationInput,
        *,
        use_git_timestamp: bool,
        timeout: float,
        default_tle: float,
        prev_result: Optional[VerifyCommandResult],
        split_state: Optional[SplitState],
        verification_time: Optional[datetime.datetime] = None,
    ) -> None:
        super().__init__(
            input=input,
            verification_time=verification_time or datetime.datetime.now().astimezone(),
            prev_result=prev_result,
            split_state=split_state,
        )
        self._input = input
        self.use_git_timestamp = use_git_timestamp
        self.timeout = timeout
        self.default_tle = default_tle
        self._result = None

    @property
    def force_result(self) -> VerifyCommandResult:
        if self._result is None:
            raise VerifierError("Not verified yet.")
        return self._result

    def get_file_timestamp(self, path: pathlib.Path) -> datetime.datetime:
        if self.use_git_timestamp:
            return github.get_commit_time(self.input.resolve_dependencies(path))
        else:
            dependicies = self.input.resolve_dependencies(path)

            timestamp = max(x.stat().st_mtime for x in dependicies)
            system_local_timezone = datetime.datetime.now().astimezone().tzinfo
            return datetime.datetime.fromtimestamp(
                timestamp, tz=system_local_timezone
            ).replace(
                microsecond=0
            )  # microsecond=0 is required because it's erased in git commit

    def verify(self, *, download: bool = True) -> VerifyCommandResult:
        start_time = datetime.datetime.now()

        logger.info(
            "current_verification_files: %s",
            " ".join(str(p) for p in self.current_verification_files.keys()),
        )
        try:
            ulimit_stack()
        except Exception:
            logger.warning("failed to increase the stack size[ulimit]")

        if self.prev_result:
            file_results = self.prev_result.files.copy()
        else:
            file_results = dict[pathlib.Path, FileResult]()

        for p, f in self.current_verification_files.items():
            logger.info("Start: %s", str(p))
            with log.group(f"Verify: {str(p)}"):
                logger.debug(repr(f))
                file_results[p] = results = FileResult()

                prev_time = datetime.datetime.now()
                try:
                    if download:
                        run_download(f, check=True, group_log=False)
                except Exception:
                    results.command_results.append(
                        self.create_command_result(ResultStatus.FAILURE, prev_time)
                    )
                    logger.error("Failed to download")
                    continue

                for command in f.verification:
                    logger.debug("command=%s", repr(command))
                    prev_time = datetime.datetime.now()
                    if (
                        self.timeout is not None
                        and (prev_time - start_time).total_seconds() > self.timeout
                    ):
                        logger.warning("Skip[Timeout]: %s, %s", p, repr(command))
                        results.command_results.append(
                            self.create_command_result(ResultStatus.SKIPPED, prev_time)
                        )
                        continue

                    try:
                        error_message: Optional[str] = None
                        if not command.run_compile_command():
                            error_message = "Failed to compile"

                        if not command.run_command(self):
                            error_message = "Failed to test"

                        if error_message:
                            logger.error("%s: %s, %s", error_message, p, repr(command))
                            results.command_results.append(
                                self.create_command_result(
                                    ResultStatus.FAILURE, prev_time
                                )
                            )
                            if github.is_in_github_actions():
                                github.print_error(
                                    message=f"{error_message} {str(p)}",
                                    file=str(p.resolve()),
                                )
                            continue
                        results.command_results.append(
                            self.create_command_result(ResultStatus.SUCCESS, prev_time)
                        )
                    except Exception as e:
                        message = (
                            e.message
                            if isinstance(e, VerifierError)
                            else "Failed to verify"
                        )
                        logger.error("%s: %s, %s", message, p, repr(command))
                        traceback.print_exc()
                        results.command_results.append(
                            self.create_command_result(ResultStatus.FAILURE, prev_time)
                        )

        self._result = VerifyCommandResult(
            total_seconds=(datetime.datetime.now() - start_time).total_seconds(),
            files=file_results,
        )
        return self._result

    def create_command_result(
        self,
        status: ResultStatus,
        prev_time: datetime.datetime,
    ) -> VerificationResult:
        elapsed = (datetime.datetime.now() - prev_time).total_seconds()
        return VerificationResult(
            status=status,
            elapsed=elapsed,
            last_execution_time=self.verification_time,
        )
