import pathlib
from abc import ABC, abstractmethod
from subprocess import CompletedProcess
from typing import Annotated, Literal, Optional, Protocol, Union

from pydantic import BaseModel, Field

import competitive_verifier.oj as oj
from competitive_verifier.exec import exec_command

_dummy_true: CompletedProcess[str] = CompletedProcess("true", 0)


class VerificationParams(Protocol):
    default_tle: float
    test_directory: pathlib.Path


class BaseCommand(BaseModel, ABC):
    @abstractmethod
    def run_command(
        self,
        params: Optional[VerificationParams] = None,
    ) -> CompletedProcess[str]:
        ...

    @abstractmethod
    def run_compile_command(
        self,
        params: Optional[VerificationParams] = None,
    ) -> CompletedProcess[str]:
        ...


class DummyCommand(BaseCommand):
    type: Literal["dummy"] = "dummy"

    def run_command(
        self,
        params: Optional[VerificationParams] = None,
    ) -> CompletedProcess[str]:
        return _dummy_true

    def run_compile_command(
        self,
        params: Optional[VerificationParams] = None,
    ) -> CompletedProcess[str]:
        return _dummy_true


class VerificationCommand(BaseCommand):
    type: Literal["command"] = "command"

    command: str
    compile: Optional[str] = None

    def run_command(
        self,
        params: Optional[VerificationParams] = None,
    ) -> CompletedProcess[str]:
        return exec_command(self.command, text=True)

    def run_compile_command(
        self,
        params: Optional[VerificationParams] = None,
    ) -> CompletedProcess[str]:
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

    def run_command(
        self,
        params: Optional[VerificationParams] = None,
    ) -> CompletedProcess[str]:
        if not params:
            raise ValueError(
                "ProblemVerificationCommand.run_command requires VerificationParams"
            )

        command = [
            "oj",
            "test",
            "-c",
            self.command,
            "-d",
            str(params.test_directory),
            "--print-input",
            "--tle",
            str(self.tle or params.default_tle),
        ]
        checker_problem = oj.get_checker_problem(self.problem)
        if checker_problem:
            command += [
                "--judge-command",
                str(checker_problem.download_checker_binary()),
            ]
        if self.error:
            command += ["-e", str(self.error)]
        return exec_command(command, text=True)

    def run_compile_command(
        self,
        params: Optional[VerificationParams] = None,
    ) -> CompletedProcess[str]:
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
