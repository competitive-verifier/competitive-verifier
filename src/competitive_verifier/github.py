import datetime
import os
import pathlib
import subprocess
import uuid
from contextlib import contextmanager
from typing import Iterable, Optional, TextIO


def is_in_github_actions() -> bool:
    return "GITHUB_ACTIONS" in os.environ


def is_enable_debug() -> bool:
    return "RUNNER_DEBUG" in os.environ


def _optional_path(strpath: Optional[str]) -> Optional[pathlib.Path]:
    return pathlib.Path(strpath) if strpath else None


def get_output_path() -> Optional[pathlib.Path]:
    strpath = os.getenv("GITHUB_OUTPUT")
    return _optional_path(strpath)


def get_workspace_path() -> Optional[pathlib.Path]:
    strpath = os.getenv("GITHUB_WORKSPACE")
    return _optional_path(strpath)


def get_step_summary_path() -> Optional[pathlib.Path]:
    strpath = os.getenv("GITHUB_STEP_SUMMARY")
    return _optional_path(strpath)


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


def set_output(name: str, value: str) -> bool:
    path = get_output_path()
    if path and path.exists():
        delimiter = "outputdelimiter_" + str(uuid.uuid4())
        with open(path, mode="a", encoding="utf-8") as fp:
            fp.write(name)
            fp.write("<<")
            fp.write(delimiter + "\n")
            fp.write(value + "\n")
            fp.write(delimiter + "\n")
        return True
    return False


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
