# Python Version: 3.x
import glob
import pathlib
from subprocess import CompletedProcess
from typing import TYPE_CHECKING, Callable, Iterator, Optional, Union

from competitive_verifier.exec import exec_command as _exec_command
from competitive_verifier.util import read_text_normalized  # noqa # pyright: ignore

if TYPE_CHECKING:
    from _typeshed import StrOrBytesPath

    _StrOrListStr = Union[str, list[str]]


def glob_with_predicate(pred: Callable[[pathlib.Path], bool]) -> Iterator[pathlib.Path]:
    """glob_with_basename iterates files whose basenames satisfy the predicate.

    This function ignores hidden directories and hidden files, whose names start with dot `.` letter.
    """
    return filter(pred, map(pathlib.Path, glob.glob("**", recursive=True)))


def exec_command(
    command: "_StrOrListStr",
    *,
    check: bool = False,
    env: Optional[dict[str, str]] = None,
    cwd: Optional["StrOrBytesPath"] = None,
) -> CompletedProcess[bytes]:
    return _exec_command(
        command,
        check=check,
        env=env,
        cwd=cwd,
        text=False,
        capture_output=True,
        group_log=False,
    )
