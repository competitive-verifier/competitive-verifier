import datetime
import pathlib
from collections.abc import Iterable
from typing import TYPE_CHECKING

from .exec import command_stdout

if TYPE_CHECKING:
    from _typeshed import StrPath


def get_commit_time(files: Iterable[pathlib.Path]) -> datetime.datetime:
    code = ["git", "log", "-1", "--date=iso", "--pretty=%ad", "--", *map(str, files)]
    stdout = command_stdout(code)
    timestamp = stdout.strip()
    if not timestamp:
        return datetime.datetime.min.replace(tzinfo=datetime.timezone.utc)
    return datetime.datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S %z")


def ls_files(*args: "StrPath") -> set[pathlib.Path]:
    stdout = command_stdout(["git", "ls-files", "-z", *[str(p) for p in (args or [])]])
    return set(map(pathlib.Path, filter(None, stdout.split("\0"))))


def get_root_directory() -> pathlib.Path:
    stdout = command_stdout(["git", "rev-parse", "--show-toplevel"])
    return pathlib.Path(stdout.strip())
