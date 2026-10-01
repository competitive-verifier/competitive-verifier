import datetime
import hashlib
import pathlib
import time
from abc import ABC, abstractmethod
from functools import cached_property
from logging import getLogger

from competitive_verifier import git, log
from competitive_verifier.download import download_files as run_download
from competitive_verifier.models import (
    BaseProblemVerification,
    FileResult,
    ResultStatus,
    VerifcationTimeoutError,
    Verification,
    VerificationFile,
    VerificationInput,
    VerificationResult,
    VerifyCommandResult,
)
from competitive_verifier.resource import try_ulimit_stack
from competitive_verifier.verify.split_state import SplitState

logger = getLogger(__name__)


def _now() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc).astimezone()


class InputContainer(ABC):
    verifications: VerificationInput
    verification_time: datetime.datetime
    prev_result: VerifyCommandResult | None
    split_state: SplitState | None
    default_tle: float | None
    default_mle: float | None

    def __init__(
        self,
        *,
        verifications: VerificationInput,
        verification_time: datetime.datetime,
        prev_result: VerifyCommandResult | None,
        split_state: SplitState | None,
        default_tle: float | None = None,
        default_mle: float | None = None,
    ) -> None:
        self.verifications = verifications
        self.verification_time = verification_time
        self.prev_result = prev_result
        self.split_state = split_state
        self.default_tle = default_tle
        self.default_mle = default_mle

    @abstractmethod
    def get_file_timestamp(self, path: pathlib.Path) -> datetime.datetime: ...

    def file_content_hash(self, path: pathlib.Path) -> str | None:
        """Digest of the file, its transitive dependencies and its verifications.

        The verifications include their effective time and memory limits
        and their test data. ``None`` if any dependency is missing.
        """
        digest = hashlib.sha256()
        f = self.verifications.files.get(path)
        if f is None:
            return None
        for dep in sorted(self.verifications.transitive_depends_on[path]):
            try:
                content = dep.read_bytes()
            except OSError:
                return None
            digest.update(dep.as_posix().encode())
            digest.update(b"\0")
            digest.update(content)
            digest.update(b"\0")
        for v in f.verification_list:
            digest.update(v.model_dump_json(exclude_none=True).encode())
            digest.update(b"\0")
            if isinstance(v, BaseProblemVerification):
                digest.update(repr(v.tle or self.default_tle).encode())
                digest.update(b"\0")
                digest.update(repr(v.mle or self.default_mle).encode())
                digest.update(b"\0")
            testdata_hash = v.testdata_hash()
            if testdata_hash is not None:
                digest.update(testdata_hash.encode())
            digest.update(b"\0")
        return digest.hexdigest()

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
            logger.info("%s needs verification. base_time: %s", path, base_time)
        else:
            logger.info("%s doesn't need verification. base_time: %s", path, base_time)
        return result

    @cached_property
    def verification_files(self) -> dict[pathlib.Path, VerificationFile]:
        """List of verification files."""
        return {
            p: f for p, f in self.verifications.files.items() if f.is_verification()
        }

    @cached_property
    def skippable_verification_files(self) -> dict[pathlib.Path, VerificationFile]:
        return {
            p: f
            for p, f in self.verification_files.items()
            if f.is_lightweight_verification()
        }

    @cached_property
    def remaining_verification_files(self) -> dict[pathlib.Path, VerificationFile]:
        """List of verification files that have not yet been verified."""
        verification_files = {
            p: f
            for p, f in self.verification_files.items()
            if p not in self.skippable_verification_files
        }

        if self.prev_result is None:
            return verification_files

        not_updated_files = {
            k
            for k, v in self.verifications.filterd_files(self.prev_result.files)
            if not self.file_need_verification(k, v)
        }
        return {
            p: f for p, f in verification_files.items() if p not in not_updated_files
        }

    @cached_property
    def current_verification_files(self) -> dict[pathlib.Path, VerificationFile]:
        """List of verification files that self should verify.

        if ``split_state`` is None the property is ``remaining_verification_files``;

        else ``split_state.split(remaining_verification_files)``.
        """
        if self.split_state is None:
            return self.remaining_verification_files

        lst = [(p, f) for p, f in self.remaining_verification_files.items()]
        lst.sort(key=lambda tup: tup[0])

        return dict(self.split_state.split(lst))


class BaseVerifier(InputContainer):
    timeout: float
    default_tle: float | None
    default_mle: float | None
    split_state: SplitState | None

    _result: VerifyCommandResult | None

    def __init__(
        self,
        verifications: VerificationInput,
        *,
        timeout: float,
        default_tle: float | None,
        default_mle: float | None,
        prev_result: VerifyCommandResult | None,
        split_state: SplitState | None,
        verification_time: datetime.datetime | None = None,
    ) -> None:
        super().__init__(
            verifications=verifications,
            verification_time=verification_time or _now(),
            prev_result=prev_result,
            split_state=split_state,
            default_tle=default_tle,
            default_mle=default_mle,
        )
        self._input = verifications
        self.timeout = timeout
        self._result = None

    @property
    def is_first(self) -> bool:
        if not self.split_state:
            return True
        return self.split_state.index == 0

    def _enumerate_verifications(
        self,
        p: pathlib.Path,
        f: VerificationFile,
        *,
        download: bool,
        deadline: float,
    ) -> list[VerificationResult]:
        logger.debug("%r", f)
        verifications = list[VerificationResult]()
        try:
            if time.perf_counter() > deadline:
                raise VerifcationTimeoutError  # noqa: TRY301
            if download:
                run_download(f, check=True, group_log=False)
        except VerifcationTimeoutError:
            verifications.append(
                self.create_command_result(ResultStatus.SKIPPED, time.perf_counter())
            )
            logger.warning("Skip[Timeout]: %s", p)
            return verifications
        except BaseException:
            verifications.append(
                self.create_command_result(ResultStatus.FAILURE, time.perf_counter())
            )
            logger.exception(
                "Failed to download: %s",
                f.verification,
                extra={"github": log.GitHubMessageParams()},
            )
            return verifications

        for ve in f.verification_list:
            logger.debug("command=%r", ve)
            prev_time = time.perf_counter()
            try:
                if prev_time > deadline:
                    raise VerifcationTimeoutError  # noqa: TRY301

                rs, error_message = self.run_verification(ve, deadline=deadline)
                if error_message:
                    logger.error(
                        "%s: %s, verification=%s",
                        error_message,
                        p,
                        ve.model_dump_json(exclude_unset=True),
                        extra={"github": log.GitHubMessageParams(file=p)},
                    )
                verifications.append(
                    self.create_command_result(rs, prev_time, name=ve.name)
                )
            except VerifcationTimeoutError:
                logger.warning("Skip[Timeout]: %s, %r", p, ve)
                verifications.append(
                    self.create_command_result(
                        ResultStatus.SKIPPED,
                        prev_time,
                        name=ve.name,
                    )
                )
            except BaseException:
                logger.exception(
                    "Failed to verify: %s, %r",
                    p,
                    ve,
                    extra={"github": log.GitHubMessageParams()},
                )
                verifications.append(
                    self.create_command_result(
                        ResultStatus.FAILURE,
                        prev_time,
                        name=ve.name,
                    )
                )
        return verifications

    def verify(self, *, download: bool = True) -> VerifyCommandResult:
        start_time = time.perf_counter()
        deadline = start_time + self.timeout

        with log.group("current_verification_files"):
            current_verification_files = self.current_verification_files
            logger.info(
                "current_verification_files: %s",
                " ".join(p.as_posix() for p in current_verification_files),
            )
        try_ulimit_stack()

        file_results: dict[pathlib.Path, FileResult] = (
            {
                k: v.model_copy(update={"newest": False})
                for k, v in self.verifications.filterd_files(self.prev_result.files)
                if k.exists()
            }
            if self.prev_result
            else {}
        )

        for p, f in current_verification_files.items():
            with log.group(f"Verify: {p.as_posix()}"):
                file_results[p] = FileResult(
                    verifications=self._enumerate_verifications(
                        p,
                        f,
                        download=download,
                        deadline=deadline,
                    ),
                    content_hash=self.file_content_hash(p),
                )

        sippable_file_results = self.skippable_results()
        self._result = VerifyCommandResult(
            total_seconds=time.perf_counter() - start_time,
            files=file_results | sippable_file_results,
        )
        return self._result

    def run_verification(
        self,
        verification: Verification,
        *,
        deadline: float = float("inf"),
    ) -> tuple[ResultStatus | VerificationResult, str | None]:
        """Run verification.

        Returns:
            tuple[ResultStatus, Optional[str]]: (Result, error_message)
        """
        if not verification.run_compile_command():
            return ResultStatus.FAILURE, "Failed to compile"

        if time.perf_counter() > deadline:
            raise VerifcationTimeoutError

        rs = verification.run(self, deadline=deadline)

        if rs.status != ResultStatus.SUCCESS:
            return rs, "Failed to test"
        return rs, None

    def skippable_results(self) -> dict[pathlib.Path, FileResult]:
        """Run skippable verification."""
        results = dict[pathlib.Path, FileResult]()
        if self.is_first:
            for p, f in self.skippable_verification_files.items():
                logger.info("Start skippable: %s", p)
                verifications = list[VerificationResult]()
                prev_time = time.perf_counter()

                for v in f.verification_list:
                    rs = self.run_verification(v)[0]
                    verifications.append(
                        self.create_command_result(rs, prev_time, name=v.name)
                    )
                results[p] = FileResult(
                    verifications=verifications,
                    content_hash=self.file_content_hash(p),
                    newest=True,
                )
        return results

    def create_command_result(
        self,
        status_or_result: ResultStatus | VerificationResult,
        prev_time: float,
        *,
        name: str | None = None,
    ) -> VerificationResult:
        if isinstance(status_or_result, VerificationResult):
            return status_or_result

        elapsed = time.perf_counter() - prev_time
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
        verifications: VerificationInput,
        *,
        timeout: float,
        default_tle: float | None,
        default_mle: float | None,
        prev_result: VerifyCommandResult | None,
        split_state: SplitState | None,
        verification_time: datetime.datetime | None = None,
        use_git_timestamp: bool,
    ) -> None:
        super().__init__(
            verifications=verifications,
            verification_time=verification_time or _now(),
            prev_result=prev_result,
            split_state=split_state,
            timeout=timeout,
            default_tle=default_tle,
            default_mle=default_mle,
        )
        self.use_git_timestamp = use_git_timestamp

    def get_file_timestamp(self, path: pathlib.Path) -> datetime.datetime:
        dependicies = self.verifications.transitive_depends_on[path]

        if self.use_git_timestamp:
            return git.get_commit_time(dependicies)

        timestamp = max(x.stat().st_mtime for x in dependicies)
        system_local_timezone = _now().tzinfo

        # microsecond=0 is required because it's erased in git commit
        return datetime.datetime.fromtimestamp(
            timestamp, tz=system_local_timezone
        ).replace(microsecond=0)
