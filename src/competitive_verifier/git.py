import datetime
import pathlib
from typing import TYPE_CHECKING, Iterable

from .exec import exec_command

if TYPE_CHECKING:
    from _typeshed import StrPath


def get_commit_time(files: Iterable[pathlib.Path]) -> datetime.datetime:
    code = ["git", "log", "-1", "--date=iso", "--pretty=%ad", "--"] + list(
        map(str, files)
    )
    stdout = exec_command(code, text=True, capture_output=True).stdout
    timestamp = stdout.strip()
    if not timestamp:
        return datetime.datetime.min.replace(tzinfo=datetime.timezone.utc)
    return datetime.datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S %z")


def ls_files(*args: "StrPath") -> set[pathlib.Path]:
    stdout = exec_command(
        ["git", "ls-files", "-z"] + list(str(p) for p in (args or [])),
        text=True,
        capture_output=True,
    ).stdout
    return set(map(pathlib.Path, filter(lambda p: p, stdout.split("\0"))))


def get_root_directory() -> pathlib.Path:
    stdout = exec_command(
        ["git", "rev-parse", "--show-toplevel"], text=True, capture_output=True
    ).stdout
    return pathlib.Path(stdout.strip())
