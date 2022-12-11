# Python Version: 3.x
import glob
import pathlib
from os import PathLike
from typing import Any, Callable, Iterator

from charset_normalizer import from_path


def glob_with_predicate(pred: Callable[[pathlib.Path], bool]) -> Iterator[pathlib.Path]:
    """glob_with_basename iterates files whose basenames satisfy the predicate.

    This function ignores hidden directories and hidden files, whose names start with dot `.` letter.
    """
    return filter(pred, map(pathlib.Path, glob.glob("**", recursive=True)))


def read_text_normalized(path: PathLike[Any]) -> str:
    return str(from_path(path).best())
