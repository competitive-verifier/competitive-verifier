import datetime
import os
import pathlib
import subprocess
from contextlib import contextmanager
from typing import Iterable, Optional, TextIO


def is_in_github_actions() -> bool:
    return "GITHUB_ACTIONS" in os.environ


def is_enable_debug() -> bool:
    return "RUNNER_DEBUG" in os.environ


def get_workspace_path() -> Optional[pathlib.Path]:
    strpath = os.getenv("GITHUB_WORKSPACE")
    return pathlib.Path(strpath) if strpath else None


def print_debug(
    message: str,
    *,
    title: Optional[str] = None,
    file: Optional[str] = None,
    col: Optional[int] = None,
    endColumn: Optional[int] = None,
    line: Optional[int] = None,
    endLine: Optional[int] = None,
    force: bool = False,
    stream: Optional[TextIO] = None,
) -> None:
    _print_github(
        "debug",
        message,
        title=title,
        file=file,
        col=col,
        endColumn=endColumn,
        line=line,
        endLine=endLine,
        force=force,
        stream=stream,
    )


def print_warning(
    message: str,
    *,
    title: Optional[str] = None,
    file: Optional[str] = None,
    col: Optional[int] = None,
    endColumn: Optional[int] = None,
    line: Optional[int] = None,
    endLine: Optional[int] = None,
    force: bool = False,
    stream: Optional[TextIO] = None,
) -> None:
    _print_github(
        "warning",
        message,
        title=title,
        file=file,
        col=col,
        endColumn=endColumn,
        line=line,
        endLine=endLine,
        force=force,
        stream=stream,
    )


def print_error(
    message: str,
    *,
    title: Optional[str] = None,
    file: Optional[str] = None,
    col: Optional[int] = None,
    endColumn: Optional[int] = None,
    line: Optional[int] = None,
    endLine: Optional[int] = None,
    force: bool = False,
    stream: Optional[TextIO] = None,
) -> None:
    _print_github(
        "error",
        message,
        title=title,
        file=file,
        col=col,
        endColumn=endColumn,
        line=line,
        endLine=endLine,
        force=force,
        stream=stream,
    )


def _print_github(
    command: str,
    message: str,
    *,
    title: Optional[str] = None,
    file: Optional[str] = None,
    col: Optional[int] = None,
    endColumn: Optional[int] = None,
    line: Optional[int] = None,
    endLine: Optional[int] = None,
    force: bool = False,
    stream: Optional[TextIO] = None,
) -> None:
    """print Github Actions style message

    https://docs.github.com/en/actions/using-workflows/workflow-commands-for-github-actions

    Args:
        title: Custom title
        file: Filename
        col: Column number, starting at 1
        endColumn: End column number
        line: Line number, starting at 1
        endLine: End line number
    """
    annotation = ",".join(
        f"{tup[0]}={tup[1]}"
        for tup in (
            ("title", title),
            ("file", file),
            ("col", col),
            ("endColumn", endColumn),
            ("line", line),
            ("endLine", endLine),
        )
        if tup[1] is not None
    )

    if force or is_in_github_actions():
        print(f"::{command} {annotation}::{message}", file=stream)


def begin_group(title: str, *, stream: Optional[TextIO] = None):
    print(f"::group::{title}", file=stream)


def end_group(*, stream: Optional[TextIO] = None):
    print("::endgroup::", file=stream)


@contextmanager
def group(title: str, *, stream: Optional[TextIO] = None):
    try:
        begin_group(title, stream=stream)
        yield
    finally:
        end_group(stream=stream)


def get_commit_time(files: Iterable[pathlib.Path]) -> datetime.datetime:
    code = ["git", "log", "-1", "--date=iso", "--pretty=%ad", "--"] + list(
        map(str, files)
    )
    timestamp = subprocess.check_output(code).decode().strip()
    if not timestamp:
        return datetime.datetime.min
    return datetime.datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S %z")
