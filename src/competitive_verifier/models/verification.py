import pathlib
from abc import ABC, abstractmethod
from typing import Annotated, Literal, Optional, Protocol, Union

from pydantic import BaseModel, Field

from .. import exec, oj


class VerificationParams(Protocol):
    default_tle: float


class BaseVerification(BaseModel, ABC):
    @abstractmethod
    def run_command(
        self,
        params: Optional[VerificationParams] = None,
    ) -> bool:
        ...

    @abstractmethod
    def run_compile_command(
        self,
        params: Optional[VerificationParams] = None,
    ) -> bool:
        ...

    @property
    def is_skippable(self) -> bool:
        return False


class DependencyVerification(BaseVerification):
    type: Literal["dependency"] = "dependency"
    dependency: pathlib.Path

    class Config:
        json_encoders = {pathlib.Path: lambda v: v.as_posix()}  # type: ignore

    @property
    def is_skippable(self) -> bool:
        return True

    def run_command(
        self,
        params: Optional[VerificationParams] = None,
    ) -> bool:
        return True

    def run_compile_command(
        self,
        params: Optional[VerificationParams] = None,
    ) -> bool:
        return True


class CommandVerification(BaseVerification):
    type: Literal["command"] = "command"

    command: str
    compile: Optional[str] = None

    def run_command(
        self,
        params: Optional[VerificationParams] = None,
    ) -> bool:
        return exec.exec_command(self.command, text=True).returncode == 0

    def run_compile_command(
        self,
        params: Optional[VerificationParams] = None,
    ) -> bool:
        if self.compile:
            return exec.exec_command(self.compile, text=True).returncode == 0
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

    def run_command(
        self,
        params: Optional[VerificationParams] = None,
    ) -> bool:
        if not params:
            raise ValueError(
                "ProblemVerification.run_command requires VerificationParams"
            )

        return oj.test(
            url=self.problem,
            command=self.command,
            tle=self.tle or params.default_tle,
            error=self.error,
        )

    def run_compile_command(
        self,
        params: Optional[VerificationParams] = None,
    ) -> bool:
        if self.compile:
            return exec.exec_command(self.compile, text=True).returncode == 0
        return True


Verification = Annotated[
    Union[
        DependencyVerification,
        CommandVerification,
        ProblemVerification,
    ],
    Field(discriminator="type"),
]
