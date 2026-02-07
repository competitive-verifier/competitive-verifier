import hashlib
import pathlib
from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import NamedTuple, Optional

from competitive_verifier import config


class TestCaseData(NamedTuple):
    name: str
    input_data: bytes
    output_data: bytes


class Problem(ABC):
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}.from_url({self.url!r})"  # pragma: no cover

    @abstractmethod
    def download_system_cases(self) -> Iterable[TestCaseData] | bool: ...

    @property
    @abstractmethod
    def url(self) -> str: ...

    @property
    def checker(self) -> pathlib.Path | None:
        return None

    @property
    def hash_id(self):
        return hashlib.md5(self.url.encode(), usedforsecurity=False).hexdigest()

    @property
    def problem_directory(self):
        return config.get_problem_cache_dir() / self.hash_id

    @property
    def test_directory(self):
        return self.problem_directory / "test"

    @classmethod
    @abstractmethod
    def from_url(cls, url: str) -> Optional["Problem"]: ...
