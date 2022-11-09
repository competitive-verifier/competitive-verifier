from abc import ABC, abstractmethod
from typing import Annotated, Literal, Optional, Protocol, Union

from pydantic import BaseModel, Field

from .. import oj
from ..exec import exec_command
from .result_status import ResultStatus


class VerificationParams(Protocol):
    default_tle: float


class BaseVerification(BaseModel, ABC):
    @abstractmethod
    def run(
        self,
        params: Optional[VerificationParams] = None,
    ) -> ResultStatus:
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

    command: str
    compile: Optional[str] = None

    def run(
        self,
        params: Optional[VerificationParams] = None,
    ) -> ResultStatus:
        if exec_command(self.command, text=True).returncode == 0:
            return ResultStatus.SUCCESS
        return ResultStatus.FAILURE

    def run_compile_command(
        self,
        params: Optional[VerificationParams] = None,
    ) -> bool:
        if self.compile:
            return exec_command(self.compile, text=True).returncode == 0
        return True


class ProblemVerification(BaseVerification):
    type: Literal["problem"] = "problem"

    command: str
    compile: Optional[str] = None

    problem: str
    """
    problem: URL of problem
    """

    error: Optional[float] = None
    tle: Optional[float] = None

    def run(
        self,
        params: Optional[VerificationParams] = None,
    ) -> ResultStatus:
        if not params:
            raise ValueError("ProblemVerification.run requires VerificationParams")

        if oj.test(
            url=self.problem,
            command=self.command,
            tle=self.tle or params.default_tle,
            error=self.error,
        ):
            return ResultStatus.SUCCESS
        return ResultStatus.FAILURE

    def run_compile_command(
        self,
        params: Optional[VerificationParams] = None,
    ) -> bool:
        if self.compile:
            return exec_command(self.compile, text=True).returncode == 0
        return True


Verification = Annotated[
    Union[
        ConstVerification,
        CommandVerification,
        ProblemVerification,
    ],
    Field(discriminator="type"),
]
