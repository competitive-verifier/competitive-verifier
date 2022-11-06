from abc import ABC, abstractmethod
from typing import Annotated, Literal, Optional, Protocol, Union

from pydantic import BaseModel, Field

from .. import exec, oj


class VerificationParams(Protocol):
    default_tle: float


class BaseCommand(BaseModel, ABC):
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


class DummyCommand(BaseCommand):
    type: Literal["dummy"] = "dummy"

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


class VerificationCommand(BaseCommand):
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


class ProblemVerificationCommand(BaseCommand):
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
                "ProblemVerificationCommand.run_command requires VerificationParams"
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


Command = Annotated[
    Union[
        DummyCommand,
        VerificationCommand,
        ProblemVerificationCommand,
    ],
    Field(discriminator="type"),
]
