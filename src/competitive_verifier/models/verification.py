from abc import ABC, abstractmethod
from typing import Annotated, Literal, Optional, Protocol, Union

from pydantic import BaseModel, Field

from competitive_verifier.exec import exec_command

from .result import VerificationResult
from .result_status import ResultStatus


class ShellCommand(BaseModel):
    command: Union[list[str], str]
    """Shell command
    """

    env: Optional[dict[str, str]] = None
    """Envitonment variables for command
    """


ShellCommandLike = Union[ShellCommand, Union[list[str], str]]


def parse_command_like(cmd: ShellCommandLike) -> ShellCommand:
    if isinstance(cmd, str) or isinstance(cmd, list):
        return ShellCommand(command=cmd)
    return cmd


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
    status: ResultStatus

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

    command: ShellCommandLike
    compile: Optional[ShellCommandLike] = None

    def run(
        self,
        params: Optional[VerificationParams] = None,
    ) -> ResultStatus:
        c = parse_command_like(self.command)
        if exec_command(c.command, env=c.env, text=True).returncode == 0:
            return ResultStatus.SUCCESS
        return ResultStatus.FAILURE

    def run_compile_command(
        self,
        params: Optional[VerificationParams] = None,
    ) -> bool:
        if self.compile:
            c = parse_command_like(self.compile)
            return exec_command(c.command, env=c.env, text=True).returncode == 0
        return True


class ProblemVerification(BaseVerification):
    type: Literal["problem"] = "problem"

    command: ShellCommandLike
    compile: Optional[ShellCommandLike] = None

    problem: str
    """
    problem: URL of problem
    """

    error: Optional[float] = None
    tle: Optional[float] = None
    mle: Optional[float] = None

    def run(
        self,
        params: Optional[VerificationParams] = None,
    ) -> VerificationResult:
        import competitive_verifier.oj as oj

        if not params:
            raise ValueError("ProblemVerification.run requires VerificationParams")

        c = parse_command_like(self.command)
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
            c = parse_command_like(self.compile)
            return exec_command(c.command, env=c.env, text=True).returncode == 0
        return True


Verification = Annotated[
    Union[
        ConstVerification,
        CommandVerification,
        ProblemVerification,
    ],
    Field(discriminator="type"),
]
