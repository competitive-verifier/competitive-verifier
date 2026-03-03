import logging
from collections.abc import Mapping
from dataclasses import astuple, dataclass
from typing import Any


@dataclass
class LogComparer:  # noqa: PLW1641
    message: str
    level: int | None = None
    args: tuple[object, ...] | Mapping[str, object] | None = None
    name: str | None = None
    extra: dict[str, Any] | None = None

    def __eq__(self, value: object) -> bool:
        if type(value) is LogComparer:
            return astuple(self) == astuple(value)

        if isinstance(value, logging.LogRecord):
            if self.level is not None and value.levelno != self.level:
                return False
            if self.args is not None and value.args != self.args:
                return False
            if self.name is not None and value.name != self.name:
                return False
            if self.extra is not None:
                for extra_key, extra_value in self.extra.items():
                    if getattr(value, extra_key, object()) != extra_value:
                        return False
            return value.getMessage() == self.message
        return NotImplemented
