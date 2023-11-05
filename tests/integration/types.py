import pathlib
from typing import Protocol

from pydantic import BaseModel


class FilePaths(BaseModel):
    root: pathlib.Path
    targets: str
    verify: str
    result: str
    dest_root: pathlib.Path


class ConfigDirFunc(Protocol):
    def __call__(
        self,
        name: str,
    ) -> pathlib.Path:
        ...
