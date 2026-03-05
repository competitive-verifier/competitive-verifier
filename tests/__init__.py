from collections.abc import Mapping
from dataclasses import astuple, dataclass, fields, replace
from logging import LogRecord

from competitive_verifier.log import GitHubMessageParams


@dataclass
class LogComparer:  # noqa: PLW1641
    message: str
    level: int | None = None
    args: tuple[object, ...] | Mapping[str, object] | None = None
    name: str | None = None
    github: GitHubMessageParams | None = None

    def fill(self, other: "LogComparer") -> "LogComparer":
        other_dict = {
            f.name: getattr(other, f.name)
            for f in fields(self)
            if f.name != "github" and getattr(self, f.name) is None
        }
        return replace(self, **other_dict)

    @staticmethod
    def from_record(value: LogRecord) -> "LogComparer":
        return LogComparer(
            message=value.getMessage(),
            level=value.levelno,
            name=value.name,
            args=value.args,
            github=getattr(value, "github", None),
        )

    def __eq__(self, value: object) -> bool:
        if isinstance(value, LogRecord):
            value = self.from_record(value)
            return astuple(self.fill(value)) == astuple(value)
        if type(value) is LogComparer:
            return astuple(self) == astuple(value)
        return NotImplemented
