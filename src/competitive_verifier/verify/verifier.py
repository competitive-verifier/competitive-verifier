import datetime
import pathlib
import traceback
from abc import ABC, abstractmethod
from functools import cached_property
from logging import getLogger
from typing import Optional, Union

from competitive_verifier import git, github, log
from competitive_verifier.download.main import run_impl as run_download
from competitive_verifier.error import VerifierError
from competitive_verifier.models import (
    FileResult,
    ResultStatus,
    Verification,
    VerificationFile,
    VerificationInput,
    VerificationResult,
    VerifyCommandResult,
)
from competitive_verifier.resource import ulimit_stack
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
        if not path.exists():
            return False
        base_time = min(self.verification_time, self.get_file_timestamp(path))
        result = file_result.need_verification(base_time)
        if result:
            logger.info(
                "%s needs verification. base_time: %s", path.as_posix(), base_time
            )
        else:
            logger.info(
                "%s doesn't need verification. base_time: %s",
                path.as_posix(),
                base_time,
            )
        return result

    @cached_property
    def verification_files(self) -> dict[pathlib.Path, VerificationFile]:
        """
        List of verification files.
        """
        return {p: f for p, f in self.input.files.items() if f.is_verification()}

    @cached_property
    def skippable_verification_files(self) -> dict[pathlib.Path, VerificationFile]:
        return {
            p: f
            for p, f in self.verification_files.items()
            if f.is_skippable_verification()
        }

    @cached_property
    def remaining_verification_files(self) -> dict[pathlib.Path, VerificationFile]:
        """
        List of verification files that have not yet been verified.
        """
        verification_files = {
            p: f
            for p, f in self.verification_files.items()
            if p not in self.skippable_verification_files
        }

        if self.prev_result is None:
            return verification_files

        not_updated_files = set(
            k
            for k, v in self.input.filterd_files(self.prev_result.files)
            if not self.file_need_verification(k, v)
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


class BaseVerifier(InputContainer):
    timeout: float
    default_tle: Optional[float]
    default_mle: Optional[float]
    split_state: Optional[SplitState]

    _result: Optional[VerifyCommandResult]

    def __init__(
        self,
        input: VerificationInput,
        *,
        timeout: float,
        default_tle: Optional[float],
        default_mle: Optional[float],
        prev_result: Optional[VerifyCommandResult],
        split_state: Optional[SplitState],
        verification_time: Optional[datetime.datetime] = None,
    ) -> None:
        super().__init__(
            input=input,
            verification_time=verification_time or self.now().astimezone(),
            prev_result=prev_result,
            split_state=split_state,
        )
        self._input = input
        self.timeout = timeout
        self.default_tle = default_tle
        self.default_mle = default_mle
        self._result = None

    @property
    def force_result(self) -> VerifyCommandResult:
        if self._result is None:
            raise VerifierError("Not verified yet.")
        return self._result

    @property
    def is_first(self) -> bool:
        if not self.split_state:
            return True
        return self.split_state.index == 0

    def now(self) -> datetime.datetime:
        return datetime.datetime.now(datetime.timezone.utc)

    def verify(self, *, download: bool = True) -> VerifyCommandResult:
        start_time = self.now()
        with log.group("current_verification_files"):
            current_verification_files = self.current_verification_files
        logger.info(
            "current_verification_files: %s",
            " ".join(p.as_posix() for p in current_verification_files.keys()),
        )
        try:
            ulimit_stack()
        except BaseException:
            logger.warning("failed to increase the stack size[ulimit]")

        if self.prev_result:
            file_results = {
                k: v.model_copy(update={"newest": False})
                for k, v in self.input.filterd_files(self.prev_result.files)
                if k.exists()
            }
        else:
            file_results = dict[pathlib.Path, FileResult]()

        for p, f in current_verification_files.items():

            def enumerate_verifications() -> list[VerificationResult]:
                logger.debug(repr(f))
                prev_time = self.now()
                verifications = list[VerificationResult]()
                try:
                    if download and not run_download(f, check=True, group_log=False):
                        raise Exception()
                except BaseException as e:
                    verifications.append(
                        self.create_command_result(ResultStatus.FAILURE, prev_time)
                    )
                    logger.exception("Failed to download", e)
                    return verifications

                for ve in f.verification_list:
                    logger.debug("command=%s", repr(ve))
                    prev_time = self.now()
                    if (prev_time - start_time).total_seconds() > self.timeout:
                        logger.warning("Skip[Timeout]: %s, %s", p, repr(ve))
                        verifications.append(
                            self.create_command_result(
                                ResultStatus.SKIPPED,
                                prev_time,
                                name=ve.name,
                            )
                        )
                        return verifications

                    try:
                        rs, error_message = self.run_verification(ve)
                        if error_message:
                            logger.error("%s: %s, %s", error_message, p, repr(ve))
                            if github.env.is_in_github_actions():
                                github.print_error(
                                    message=f"{error_message} {p.as_posix()}",
                                    file=str(p.resolve()),
                                )
                        verifications.append(
                            self.create_command_result(rs, prev_time, name=ve.name)
                        )
                    except BaseException as e:
                        message = (
                            e.message
                            if isinstance(e, VerifierError)
                            else "Failed to verify"
                        )
                        logger.error("%s: %s, %s", message, p, repr(ve))
                        traceback.print_exc()
                        verifications.append(
                            self.create_command_result(
                                ResultStatus.FAILURE,
                                prev_time,
                                name=ve.name,
                            )
                        )
                return verifications

            with log.group(f"Verify: {p.as_posix()}"):
                file_results[p] = FileResult(verifications=enumerate_verifications())

        sippable_file_results = self.skippable_results()
        self._result = VerifyCommandResult(
            total_seconds=(self.now() - start_time).total_seconds(),
            files=file_results | sippable_file_results,
        )
        return self._result

    def run_verification(
        self, verification: Verification
    ) -> tuple[Union[ResultStatus, VerificationResult], Optional[str]]:
        """Run verification

        Returns:
            tuple[ResultStatus, Optional[str]]: (Result, error_message)
        """
        if not verification.run_compile_command():
            return ResultStatus.FAILURE, "Failed to compile"

        rs = verification.run(self)

        if rs.status != ResultStatus.SUCCESS:
            return rs, "Failed to test"
        return rs, None

    def skippable_results(self) -> dict[pathlib.Path, FileResult]:
        """
        Run skippable verification
        """
        results = dict[pathlib.Path, FileResult]()
        if self.is_first:
            for p, f in self.skippable_verification_files.items():
                logger.info("Start skippable: %s", p.as_posix())
                verifications = list[VerificationResult]()
                prev_time = self.now()

                for v in f.verification_list:
                    rs = self.run_verification(v)[0]
                    verifications.append(
                        self.create_command_result(rs, prev_time, name=v.name)
                    )
                results[p] = FileResult(
                    verifications=verifications,
                    newest=True,
                )
        return results

    def create_command_result(
        self,
        status_or_result: Union[ResultStatus, VerificationResult],
        prev_time: datetime.datetime,
        *,
        name: Optional[str] = None,
    ) -> VerificationResult:
        if isinstance(status_or_result, VerificationResult):
            return status_or_result

        elapsed = (self.now() - prev_time).total_seconds()
        return VerificationResult(
            verification_name=name,
            status=status_or_result,
            elapsed=elapsed,
            last_execution_time=self.verification_time,
        )


class Verifier(BaseVerifier):
    use_git_timestamp: bool

    def __init__(
        self,
        input: VerificationInput,
        *,
        timeout: float,
        default_tle: Optional[float],
        default_mle: Optional[float],
        prev_result: Optional[VerifyCommandResult],
        split_state: Optional[SplitState],
        verification_time: Optional[datetime.datetime] = None,
        use_git_timestamp: bool,
    ) -> None:
        super().__init__(
            input=input,
            verification_time=verification_time or self.now().astimezone(),
            prev_result=prev_result,
            split_state=split_state,
            timeout=timeout,
            default_tle=default_tle,
            default_mle=default_mle,
        )
        self.use_git_timestamp = use_git_timestamp

    def get_file_timestamp(self, path: pathlib.Path) -> datetime.datetime:
        if self.use_git_timestamp:
            return git.get_commit_time(self.input.transitive_depends_on[path])
        else:
            dependicies = self.input.transitive_depends_on[path]

            timestamp = max(x.stat().st_mtime for x in dependicies)
            system_local_timezone = self.now().astimezone().tzinfo
            return datetime.datetime.fromtimestamp(
                timestamp, tz=system_local_timezone
            ).replace(
                microsecond=0
            )  # microsecond=0 is required because it's erased in git commit
