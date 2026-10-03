import hashlib
import pathlib
from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import NamedTuple, Optional, cast

from competitive_verifier import config


class TestCaseFile(NamedTuple):
    name: str
    input_path: pathlib.Path
    output_path: pathlib.Path


class TestCaseData(NamedTuple):
    name: str
    input_data: bytes
    output_data: bytes


class TestCaseProvider(ABC):
    @abstractmethod
    def download_system_cases(self) -> Iterable[TestCaseData] | bool: ...

    @abstractmethod
    def iter_system_cases(self) -> Iterable[TestCaseFile]: ...

    def is_testdata_cached(self) -> bool:
        """Whether the test data is present locally (best effort).

        Must not download anything. ``True`` only means that some test data
        exists in the local cache, not that it's up to date:
        ``download_system_cases`` may still refresh it.
        """
        return True

    @property
    def checker(self) -> pathlib.Path | None:
        return None

    def sync_testdata(self) -> None:
        """Fetch the latest upstream test data identity so ``testdata_hash`` reflects it.

        Only for providers whose test data can change upstream; no-op otherwise.
        """
        return

    def testdata_hash(self) -> str | None:
        """Digest identifying the test data currently present in the local cache.

        Must not download anything. ``None`` if the provider never expects test
        data to change, or it isn't downloaded yet; the hash-based prev-result
        check then assumes the test data is unchanged.
        """
        return None


class Problem(TestCaseProvider):
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}.from_url({self.url!r})"

    def __hash__(self) -> int:  # pragma: no cover
        return hash(self.url) ^ hash(type(self))

    def __eq__(self, value: object) -> bool:
        if type(self) is not type(value):
            return False
        return self.url == cast("Problem", value).url

    @property
    @abstractmethod
    def url(self) -> str: ...

    @classmethod
    @abstractmethod
    def from_url(cls, url: str) -> Optional["Problem"]: ...

    @property
    def hash_id(self):
        return hashlib.md5(self.url.encode(), usedforsecurity=False).hexdigest()

    @property
    def problem_directory(self):
        return config.get_problem_cache_dir() / self.hash_id

    @property
    def test_directory(self):
        return self.problem_directory / "test"
