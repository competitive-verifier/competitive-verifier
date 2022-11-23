import pathlib
from typing import Optional


def to_relative(path: pathlib.Path) -> Optional[pathlib.Path]:
    try:
        return path.resolve().relative_to(pathlib.Path.cwd())
    except ValueError:
        return None
