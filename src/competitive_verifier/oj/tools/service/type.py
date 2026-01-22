from abc import ABC, abstractmethod
from typing import (
    NamedTuple,
    Optional,
)


class NotLoggedInError(RuntimeError):
    def __init__(self, message: str = "login required"):
        super().__init__(message)


class Language(NamedTuple):
    name: str


class TestCase(NamedTuple):
    name: str
    input_name: str
    input_data: bytes
    output_name: str
    output_data: bytes


class Problem(ABC):
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}.from_url({self.get_url()!r})"  # pragma: no cover

    @abstractmethod
    def download_system_cases(
        self, *, headers: dict[str, str] | None = None
    ) -> list[TestCase]:
        raise NotImplementedError

    @abstractmethod
    def get_url(self) -> str:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def from_url(cls, url: str) -> Optional["Problem"]: ...
