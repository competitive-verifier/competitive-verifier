import pathlib
from typing import Literal, TextIO


def debug(message: str, *, stream: TextIO | None = None):
    print("::debug::" + message.replace("\n", "\\n"), file=stream)


def message(
    command: Literal["error", "warning", "notice"],
    message: str,
    *,
    title: str | None = None,
    file: str | pathlib.Path | None = None,
    col: int | None = None,
    end_column: int | None = None,
    line: int | None = None,
    end_line: int | None = None,
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
        stream: Output stream
    """
    annotation = ",".join(
        f"{name}={value}"
        for name, value in (
            ("title", title),
            ("file", file.absolute() if isinstance(file, pathlib.Path) else file),
            ("col", col),
            ("endColumn", end_column),
            ("line", line),
            ("endLine", end_line),
        )
        if value is not None
    )

    print(f"::{command} {annotation}::{message}", file=stream)


def begin_group(title: str, *, stream: TextIO | None = None):
    print(f"::group::{title}", file=stream)


def end_group(*, stream: TextIO | None = None):
    print("::endgroup::", file=stream)
