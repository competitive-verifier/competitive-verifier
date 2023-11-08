import pathlib
from typing import Protocol

from pydantic import BaseModel


class FilePaths(BaseModel):
    root: pathlib.Path
    dest_root: pathlib.Path


class ConfigDirSetter(Protocol):
    def __call__(
        self,
        name: str,
    ) -> pathlib.Path:
        ...
