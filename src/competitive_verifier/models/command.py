from typing import Any, Optional


class VerificationCommand:
    command: str

    def __init__(self, *, command: str):
        self.command = command


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
        self.error = error
        self.problem = problem
        self.tle = tle


def decode(d: dict[Any, Any]) -> VerificationCommand:
    d = d.copy()
    t = d.get("type")
    del d["type"]
    if t == "problem":
        return ProblemVerificationCommand(**d)
    else:
        return VerificationCommand(**d)
