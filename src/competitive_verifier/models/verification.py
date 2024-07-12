from abc import ABC, abstractmethod
from typing import Annotated, Literal, Optional, Protocol, Union

from pydantic import BaseModel, Field

from .path import ForcePosixPath
from .result import VerificationResult
from .result_status import ResultStatus
from .shell import ShellCommand, ShellCommandLike


class VerificationParams(Protocol):
    default_tle: Optional[float]
    default_mle: Optional[float]


class BaseVerification(BaseModel, ABC):
    name: Optional[str] = None

    @abstractmethod
    def run(
        self,
        params: Optional[VerificationParams] = None,
    ) -> Union[ResultStatus, VerificationResult]:
        ...

    @abstractmethod
    def run_compile_command(
        self,
        params: Optional[VerificationParams] = None,
    ) -> bool:
        ...

    @property
    def is_skippable(self) -> bool:
        """
        If verification cost is small, it is skippable.
        """
        return False


class ConstVerification(BaseVerification):
    type: Literal["const"] = "const"
    status: ResultStatus = Field(description="The pre-defined result.")
    """The pre-defined result.
    """

    @property
    def is_skippable(self) -> bool:
        return True

    def run(
        self,
        params: Optional[VerificationParams] = None,
    ) -> ResultStatus:
        return self.status

    def run_compile_command(
        self,
        params: Optional[VerificationParams] = None,
    ) -> bool:
        return True


class CommandVerification(BaseVerification):
    type: Literal["command"] = "command"

    command: ShellCommandLike = Field(description="The shell command for verification.")
    """The shell command for verification.
    """
    compile: Optional[ShellCommandLike] = Field(
        default=None,
        description="The shell command for compile.",
    )
    """The shell command for compile.
    """

    tempdir: Optional[ForcePosixPath] = Field(
        default=None,
        description="The temporary directory for running verification.",
    )
    """The temporary directory for running verification.
    """

    def run(
        self,
        params: Optional[VerificationParams] = None,
    ) -> ResultStatus:
        if self.tempdir:
            self.tempdir.mkdir(parents=True, exist_ok=True)
        c = ShellCommand.parse_command_like(self.command)
        if c.exec_command(text=True).returncode == 0:
            return ResultStatus.SUCCESS
        return ResultStatus.FAILURE

    def run_compile_command(
        self,
        params: Optional[VerificationParams] = None,
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
    compile: Optional[ShellCommandLike] = Field(
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

    error: Optional[float] = Field(
        default=None,
        examples=[1e-9],
        description="The absolute or relative error to be considered as correct.",
    )
    """The absolute or relative error to be considered as correct.
    """
    tle: Optional[float] = Field(
        default=None,
        examples=[10],
        description="The TLE time in seconds.",
    )
    """The TLE time in seconds.
    """
    mle: Optional[float] = Field(
        default=None,
        examples=[64],
        description="The MLE memory size in megabytes.",
    )
    """The MLE memory size in megabytes.
    """

    def run(
        self,
        params: Optional[VerificationParams] = None,
    ) -> VerificationResult:
        import competitive_verifier.oj as oj

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
        )
        result.verification_name = self.name
        return result

    def run_compile_command(
        self,
        params: Optional[VerificationParams] = None,
    ) -> bool:
        if self.compile:
            c = ShellCommand.parse_command_like(self.compile)
            return c.exec_command(text=True).returncode == 0
        return True


Verification = Annotated[
    Union[
        ConstVerification,
        CommandVerification,
        ProblemVerification,
    ],
    Field(discriminator="type"),
]
