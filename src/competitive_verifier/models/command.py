from abc import ABC, abstractmethod
from typing import Annotated, Literal, Optional, Union

from pydantic import BaseModel, Field


class BaseCommand(BaseModel, ABC):
    @property
    @abstractmethod
    def get_command(self) -> Optional[str]:
        ...

    @property
    @abstractmethod
    def get_compile_command(self) -> Optional[str]:
        ...


class DummyCommand(BaseCommand):
    type: Literal["dummy"] = "dummy"

    @property
    def get_command(self) -> None:
        return None

    @property
    def get_compile_command(self) -> None:
        return None


class VerificationCommand(BaseCommand):
    type: Literal["command"] = "command"

    command: str
    compile: Optional[str] = None

    @property
    def get_command(self) -> str:
        return self.command

    @property
    def get_compile_command(self) -> Optional[str]:
        return self.compile


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

    @property
    def get_command(self) -> str:
        return self.command

    @property
    def get_compile_command(self) -> Optional[str]:
        return self.compile


Command = Annotated[
    Union[
        DummyCommand,
        VerificationCommand,
        ProblemVerificationCommand,
    ],
    Field(discriminator="type"),
]
