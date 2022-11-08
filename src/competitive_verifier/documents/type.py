import enum
import pathlib
from typing import Any

from pydantic import BaseModel


class FileStatus(enum.Enum):
    LIBRARY_ALL_AC = enum.auto()
    LIBRARY_PARTIAL_AC = enum.auto()
    LIBRARY_SOME_WA = enum.auto()
    LIBRARY_ALL_WA = enum.auto()
    LIBRARY_NO_TESTS = enum.auto()
    TEST_ACCEPTED = enum.auto()
    TEST_WRONG_ANSWER = enum.auto()
    TEST_WAITING_JUDGE = enum.auto()


class SiteRenderConfig(BaseModel):
    static_dir: pathlib.Path
    index_md: pathlib.Path
    destination_dir: pathlib.Path
    config_yml: dict[str, Any]
