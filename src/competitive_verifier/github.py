import os
import pathlib
import re
import uuid
from contextlib import contextmanager
from typing import TextIO


def _optional_path(strpath: str | None) -> pathlib.Path | None:
    return pathlib.Path(strpath) if strpath else None


class env:
    @classmethod
    def is_in_github_actions(cls) -> bool:
        return os.getenv("GITHUB_ACTIONS") == "true"

    @classmethod
    def is_enable_debug(cls) -> bool:
        return os.getenv("GITHUB_ACTIONS") == "1"

    @classmethod
    def get_ref_name(cls) -> str | None:
        return os.getenv("GITHUB_REF_NAME")

    @classmethod
    def get_api_token(cls) -> str | None:
        return os.getenv("GITHUB_TOKEN")

    @classmethod
    def get_event_name(cls) -> str | None:
        return os.getenv("GITHUB_EVENT_NAME")

    @classmethod
    def get_api_url(cls) -> str | None:
        return os.getenv("GITHUB_API_URL")

    @classmethod
    def get_repository(cls) -> str | None:
        return os.getenv("GITHUB_REPOSITORY")

    @classmethod
    def get_workflow_name(cls) -> str | None:
        return os.getenv("GITHUB_WORKFLOW")

    @classmethod
    def get_workflow_ref(cls) -> str | None:
        return os.getenv("GITHUB_WORKFLOW_REF")

    @classmethod
    def get_workflow_filename(cls) -> str | None:
        ref = cls.get_workflow_ref()
        if not ref:
            return None
        return re.sub(r".*/([^/]+\.yml)@.*$", r"\1", ref)

    @classmethod
    def get_output_path(cls) -> pathlib.Path | None:
        strpath = os.getenv("GITHUB_OUTPUT")
        return _optional_path(strpath)

    @classmethod
    def get_workspace_path(cls) -> pathlib.Path | None:
        strpath = os.getenv("GITHUB_WORKSPACE")
        return _optional_path(strpath)

    @classmethod
    def get_step_summary_path(cls) -> pathlib.Path | None:
        strpath = os.getenv("GITHUB_STEP_SUMMARY")
        return _optional_path(strpath)


def print_debug(
    message: str,
    *,
    title: str | None = None,
    file: str | None = None,
    col: int | None = None,
    end_column: int | None = None,
    line: int | None = None,
    end_line: int | None = None,
    force: bool = False,
    stream: TextIO | None = None,
) -> None:
    _print_github(
        "debug",
        message,
        title=title,
        file=file,
        col=col,
        end_column=end_column,
        line=line,
        end_line=end_line,
        force=force,
        stream=stream,
    )


def print_warning(
    message: str,
    *,
    title: str | None = None,
    file: str | None = None,
    col: int | None = None,
    end_column: int | None = None,
    line: int | None = None,
    end_line: int | None = None,
    force: bool = False,
    stream: TextIO | None = None,
) -> None:
    _print_github(
        "warning",
        message,
        title=title,
        file=file,
        col=col,
        end_column=end_column,
        line=line,
        end_line=end_line,
        force=force,
        stream=stream,
    )


def print_error(
    message: str,
    *,
    title: str | None = None,
    file: str | None = None,
    col: int | None = None,
    end_column: int | None = None,
    line: int | None = None,
    end_line: int | None = None,
    force: bool = False,
    stream: TextIO | None = None,
) -> None:
    _print_github(
        "error",
        message,
        title=title,
        file=file,
        col=col,
        end_column=end_column,
        line=line,
        end_line=end_line,
        force=force,
        stream=stream,
    )


def _print_github(
    command: str,
    message: str,
    *,
    title: str | None = None,
    file: str | None = None,
    col: int | None = None,
    end_column: int | None = None,
    line: int | None = None,
    end_line: int | None = None,
    force: bool = False,
    stream: TextIO | None = None,
) -> None:
    """Print Github Actions style message.

    https://docs.github.com/en/actions/using-workflows/workflow-commands-for-github-actions

    Args:
        command: Command name (e.g., "error", "warning", "debug")
        message: Message body
    Keyword Args:
        title: Custom title
        file: Filename
        col: Column number, starting at 1
        end_column: End column number
        line: Line number, starting at 1
        end_line: End line number
        force: If True, print the message even outside GitHub Actions
        stream: Output stream
    """
    annotation = ",".join(
        f"{tup[0]}={tup[1]}"
        for tup in (
            ("title", title),
            ("file", file),
            ("col", col),
            ("endColumn", end_column),
            ("line", line),
            ("endLine", end_line),
        )
        if tup[1] is not None
    )

    if force or env.is_in_github_actions():
        print(f"::{command} {annotation}::{message}", file=stream)


def begin_group(title: str, *, stream: TextIO | None = None):
    print(f"::group::{title}", file=stream)


def end_group(*, stream: TextIO | None = None):
    print("::endgroup::", file=stream)


def set_output(name: str, value: str) -> bool:
    path = env.get_output_path()
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
def group(title: str, *, stream: TextIO | None = None):
    try:
        begin_group(title, stream=stream)
        yield
    finally:
        end_group(stream=stream)
