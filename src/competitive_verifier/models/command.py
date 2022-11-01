import json
import pathlib
from typing import Any, Optional, Union

PathLike = Union[str, pathlib.Path]


class VerificationCommand:
    command: str

    def __init__(self, *, command: str):
        self.command = command

    @classmethod
    @property
    def type(cls) -> str:
        return "command"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, VerificationCommand):
            return self.command == other.command
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self.type + ":" + self.command)

    def __repr__(self) -> str:
        return f"VerificationCommand(command={repr(self.command)})"

    def to_json(self) -> str:
        d = self.__dict__.copy()
        d["type"] = self.type
        return json.dumps(d)


class ProblemVerificationCommand(VerificationCommand):
    problem: str
    error: Optional[float]
    tle: Optional[float]

    def __init__(
        self,
        *,
        command: str,
        problem: str,
        error: Optional[float] = None,
        tle: Optional[float] = None,
    ):
        super().__init__(command=command)
        self.problem = problem
        self.error = error
        self.tle = tle

    def __eq__(self, other: object) -> bool:
        if isinstance(other, ProblemVerificationCommand):
            return (
                self.command == other.command
                and self.problem == other.problem
                and self.error == other.error
                and self.tle == other.tle
            )
        return NotImplemented

    @classmethod
    @property
    def type(cls) -> str:
        return "problem"

    def __repr__(self) -> str:
        return f"ProblemVerificationCommand(command={repr(self.command)},error={repr(self.error)},problem={repr(self.problem)},tle={repr(self.tle)})"


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
        return f"VerificationFile(paths={[list(map(str, self.paths))]}, verification={self.verification})"
