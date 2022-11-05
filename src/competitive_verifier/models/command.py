from abc import ABC, abstractmethod
from subprocess import CompletedProcess
from typing import Annotated, Literal, Optional, Union

from pydantic import BaseModel, Field

from competitive_verifier.exec import exec_command

_dummy_true: CompletedProcess[str] = CompletedProcess("true", 0)


class BaseCommand(BaseModel, ABC):
    @abstractmethod
    def run_command(self) -> CompletedProcess[str]:
        ...

    @abstractmethod
    def run_compile_command(self) -> CompletedProcess[str]:
        ...


class DummyCommand(BaseCommand):
    type: Literal["dummy"] = "dummy"

    def run_command(self) -> CompletedProcess[str]:
        return _dummy_true

    def run_compile_command(self) -> CompletedProcess[str]:
        return _dummy_true


class VerificationCommand(BaseCommand):
    type: Literal["command"] = "command"

    command: str
    compile: Optional[str] = None

    def run_command(self) -> CompletedProcess[str]:
        return exec_command(self.command, text=True)

    def run_compile_command(self) -> CompletedProcess[str]:
        if self.compile:
            return exec_command(self.compile, text=True)
        return _dummy_true


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

    def run_command(self) -> CompletedProcess[str]:
        return exec_command(self.command, text=True)

    def run_compile_command(self) -> CompletedProcess[str]:
        if self.compile:
            return exec_command(self.compile, text=True)
        return _dummy_true


Command = Annotated[
    Union[
        DummyCommand,
        VerificationCommand,
        ProblemVerificationCommand,
    ],
    Field(discriminator="type"),
]
