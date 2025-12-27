import pathlib
from os import PathLike
from typing import Any

from charset_normalizer import (
    from_bytes,
    from_path,  # pyright: ignore[reportUnknownVariableType]
)


def to_relative(path: pathlib.Path) -> pathlib.Path | None:
    try:
        return path.resolve().relative_to(pathlib.Path.cwd())
    except ValueError:
        return None


def read_text_normalized(path: PathLike[Any]) -> str:
    return str(from_path(path).best())


def normalize_bytes_text(b: bytes) -> str:
    return str(from_bytes(b).best())
