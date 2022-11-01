import datetime
import os
import pathlib
import subprocess
import sys
from contextlib import contextmanager
from typing import Iterable, Optional


def is_in_github_actions() -> bool:
    return "GITHUB_ACTION" in os.environ


def is_enable_debug() -> bool:
    return "ACTIONS_STEP_DEBUG" in os.environ


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
    use_stderr: bool = False,
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
        use_stderr=use_stderr,
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
    use_stderr: bool = False,
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
        use_stderr=use_stderr,
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
    use_stderr: bool = False,
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
        use_stderr=use_stderr,
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
    use_stderr: bool = False,
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

    print_file = sys.stderr if use_stderr else None
    if force or is_in_github_actions():
        print(f"::{command} {annotation}::{message}", file=print_file)


def begin_group(title: str, *, use_stderr: bool = False):
    file = sys.stderr if use_stderr else None
    print(f"::group::{title}", file=file)


def end_group(*, use_stderr: bool = False):
    file = sys.stderr if use_stderr else None
    print("::endgroup::", file=file)


@contextmanager
def group(title: str, *, use_stderr: bool = False):
    try:
        begin_group(title, use_stderr=use_stderr)
        yield
    finally:
        end_group(use_stderr=use_stderr)


def get_commit_time(files: Iterable[pathlib.Path]) -> datetime.datetime:
    code = ["git", "log", "-1", "--date=iso", "--pretty=%ad", "--"] + list(
        map(str, files)
    )
    timestamp = subprocess.check_output(code).decode().strip()
    if not timestamp:
        return datetime.datetime.min
    return datetime.datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S %z")
