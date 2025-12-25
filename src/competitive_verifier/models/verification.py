from abc import ABC, abstractmethod
from typing import Annotated, Literal, Protocol

from pydantic import BaseModel, Field

from .path import ForcePosixPath
from .result import VerificationResult
from .result_status import ResultStatus
from .shell import ShellCommand, ShellCommandLike


class VerifcationTimeoutException(Exception):
    pass


class VerificationParams(Protocol):
    default_tle: float | None
    default_mle: float | None


class BaseVerification(BaseModel, ABC):
    name: str | None = None

    @abstractmethod
    def run(
        self,
        params: VerificationParams | None = None,
        *,
        deadline: float = float("inf"),
    ) -> ResultStatus | VerificationResult: ...

    @abstractmethod
    def run_compile_command(
        self,
        params: VerificationParams | None = None,
    ) -> bool: ...

    @property
    def is_lightweight(self) -> bool:
        """The verification is lightweight."""
        return False


class ConstVerification(BaseVerification):
    type: Literal["const"] = "const"
    status: ResultStatus = Field(description="The pre-defined result.")
    """The pre-defined result.
    """

    @property
    def is_lightweight(self) -> bool:
        return True

    def run(
        self,
        params: VerificationParams | None = None,
        *,
        deadline: float = float("inf"),
    ) -> ResultStatus:
        return self.status

    def run_compile_command(
        self,
        params: VerificationParams | None = None,
    ) -> bool:
        return True


class CommandVerification(BaseVerification):
    type: Literal["command"] = "command"

    command: ShellCommandLike = Field(description="The shell command for verification.")
    """The shell command for verification.
    """
    compile: ShellCommandLike | None = Field(
        default=None,
        description="The shell command for compile.",
    )
    """The shell command for compile.
    """

    tempdir: ForcePosixPath | None = Field(
        default=None,
        description="The temporary directory for running verification.",
    )
    """The temporary directory for running verification.
    """

    def run(
        self,
        params: VerificationParams | None = None,
        *,
        deadline: float = float("inf"),
    ) -> ResultStatus:
        if self.tempdir:
            self.tempdir.mkdir(parents=True, exist_ok=True)
        c = ShellCommand.parse_command_like(self.command)
        if c.exec_command(text=True).returncode == 0:
            return ResultStatus.SUCCESS
        return ResultStatus.FAILURE

    def run_compile_command(
        self,
        params: VerificationParams | None = None,
    ) -> bool:
        if self.compile:
            if self.tempdir:
                self.tempdir.mkdir(parents=True, exist_ok=True)
            c = ShellCommand.parse_command_like(self.compile)
            return c.exec_command(text=True).returncode == 0
        return True


class ProblemVerification(BaseVerification):
    type: Literal["problem"] = "problem"

    command: ShellCommandLike = Field(description="The shell command for verification.")
    """The shell command for verification.
    """
    compile: ShellCommandLike | None = Field(
        default=None,
        description="The shell command for compile.",
    )
    """The shell command for compile.
    """

    problem: str = Field(
        description="The URL of problem.",
    )
    """
    problem: URL of problem
    """

    error: float | None = Field(
        default=None,
        examples=[1e-9],
        description="The absolute or relative error to be considered as correct.",
    )
    """The absolute or relative error to be considered as correct.
    """
    tle: float | None = Field(
        default=None,
        examples=[10],
        description="The TLE time in seconds.",
    )
    """The TLE time in seconds.
    """
    mle: float | None = Field(
        default=None,
        examples=[64],
        description="The MLE memory size in megabytes.",
    )
    """The MLE memory size in megabytes.
    """

    def run(
        self,
        params: VerificationParams | None = None,
        *,
        deadline: float = float("inf"),
    ) -> VerificationResult:
        from competitive_verifier import oj  # noqa: PLC0415

        if not params:
            raise ValueError("ProblemVerification.run requires VerificationParams")

        c = ShellCommand.parse_command_like(self.command)
        result = oj.test(
            url=self.problem,
            command=c.command,
            env=c.env,
            tle=self.tle or params.default_tle,
            error=self.error,
            mle=self.mle or params.default_mle,
            deadline=deadline,
        )
        result.verification_name = self.name
        return result

    def run_compile_command(
        self,
        params: VerificationParams | None = None,
    ) -> bool:
        if self.compile:
            c = ShellCommand.parse_command_like(self.compile)
            return c.exec_command(text=True).returncode == 0
        return True


Verification = Annotated[
    ConstVerification | CommandVerification | ProblemVerification,
    Field(discriminator="type"),
]
