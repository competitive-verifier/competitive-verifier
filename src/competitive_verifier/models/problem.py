import hashlib
from abc import ABC, abstractmethod
from functools import cache
from typing import NamedTuple, Optional


class TestCase(NamedTuple):
    name: str
    input_name: str
    input_data: bytes
    output_name: str
    output_data: bytes


class Problem(ABC):
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}.from_url({self.url!r})"  # pragma: no cover

    @abstractmethod
    def download_system_cases(self) -> list[TestCase]: ...

    @property
    @abstractmethod
    def url(self) -> str: ...

    @property
    def hash_id(self):
        return hashlib.md5(self.url.encode(), usedforsecurity=False).hexdigest()

    @cache
    @staticmethod
    def _from_url(url: str) -> Optional["Problem"]:
        for ch in Problem.__subclasses__():
            if (problem := ch.from_url(url)) is not None:
                return problem
        return None

    @classmethod
    def from_url(cls, url: str) -> Optional["Problem"]:
        """Try getting problem.

        Examples:
            url: https://judge.yosupo.jp/problem/unionfind
        """
        if cls != Problem:
            raise RuntimeError("from_url must be overriden")

        return cls._from_url(url)
