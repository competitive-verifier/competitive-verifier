import pathlib
from os import PathLike
from typing import Any, Optional

from charset_normalizer import from_path


def to_relative(path: pathlib.Path) -> Optional[pathlib.Path]:
    try:
        return path.resolve().relative_to(pathlib.Path.cwd())
    except ValueError:
        return None


def read_text_normalized(path: PathLike[Any]) -> str:
    return str(from_path(path).best())
