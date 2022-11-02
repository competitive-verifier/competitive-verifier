import json
import pathlib
from abc import ABC, abstractmethod
from typing import Any, Optional, Union

PathLike = Union[str, pathlib.Path]


class Command(ABC):
    @classmethod
    @property
    @abstractmethod
    def type(cls) -> str:
        pass


class DummyCommand(Command):
    @classmethod
    @property
    def type(cls) -> str:
        return "dummy"


class VerificationCommand(Command):
    command: str
    compile: Optional[str]

    def __init__(self, *, command: str, compile: Optional[str] = None):
        self.command = command
        self.compile = compile

    @classmethod
    @property
    def type(cls) -> str:
        return "command"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, VerificationCommand):
            return self.command == other.command and self.compile == other.compile
        return NotImplemented

    def __repr__(self) -> str:
        args = ",".join(
            (
                "command=" + repr(self.command),
                "compile=" + repr(self.compile),
            )
        )
        return f"VerificationCommand({args})"

    def to_json(self) -> str:
        d = vars(self).copy()
        d["type"] = self.type
        return json.dumps(d)


class ProblemVerificationCommand(VerificationCommand):
    problem: str
    """
    problem: URL of problem
    """

    error: Optional[float]
    tle: Optional[float]

    def __init__(
        self,
        *,
        command: str,
        problem: str,
        compile: Optional[str] = None,
        error: Optional[float] = None,
        tle: Optional[float] = None,
    ):
        super().__init__(command=command, compile=compile)
        self.problem = problem
        self.error = error
        self.tle = tle

    def __eq__(self, other: object) -> bool:
        if isinstance(other, ProblemVerificationCommand):
            return (
                self.command == other.command
                and self.problem == other.problem
                and self.compile == other.compile
                and self.error == other.error
                and self.tle == other.tle
            )
        return NotImplemented

    @classmethod
    @property
    def type(cls) -> str:
        return "problem"

    def __repr__(self) -> str:
        args = ",".join(
            (
                "command=" + repr(self.command),
                "problem=" + repr(self.problem),
                "compile=" + repr(self.compile),
                "error=" + repr(self.error),
                "tle=" + repr(self.tle),
            )
        )
        return f"ProblemVerificationCommand({args})"


def decode(d: dict[Any, Any]) -> VerificationCommand:
    d = d.copy()
    t = d.get("type")
    del d["type"]
    if t == "problem":
        return ProblemVerificationCommand(**d)
    else:
        return VerificationCommand(**d)


class Verification:
    paths: list[pathlib.Path]
    command: VerificationCommand

    def __init__(
        self,
        paths: list[PathLike],
        verification: VerificationCommand,
    ):
        self.paths = list(map(pathlib.Path, paths))
        self.verification = verification

    def __repr__(self) -> str:
        args = ",".join(
            (
                "paths=" + repr([list(map(str, self.paths))]),
                "verification=" + repr(self.verification),
            )
        )
        return f"Verification({args})"
