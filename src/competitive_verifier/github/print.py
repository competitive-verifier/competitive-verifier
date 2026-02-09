from typing import Literal, TextIO

from . import env


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
    command: Literal["error", "warning", "debug"],
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
    if force or env.is_in_github_actions():
        annotation = ",".join(
            f"{name}={value}"
            for name, value in (
                ("title", title),
                ("file", file),
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
