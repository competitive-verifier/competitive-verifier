import pathlib
import sys
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from logging import (
    DEBUG,
    ERROR,
    INFO,
    NOTSET,
    WARNING,
    Handler,
    LogRecord,
    basicConfig,
)
from typing import TextIO

import colorlog
from colorama import Fore, Style

from competitive_verifier import github


@dataclass
class GitHubMessageParams:
    title: str | None = None
    file: str | pathlib.Path | None = None
    col: int | None = None
    end_column: int | None = None
    line: int | None = None
    end_line: int | None = None


class GitHubActionsHandler(Handler):
    def __init__(self, level: int | str = NOTSET) -> None:
        super().__init__(level)

    def emit(self, record: LogRecord) -> None:
        if record.levelno >= ERROR:
            command = "error"
        elif record.levelno >= WARNING:
            command = "warning"
        elif record.levelno >= INFO:
            command = "notice"
        else:
            if record.levelno >= DEBUG:
                other_name = (
                    ""
                    if record.name.startswith("competitive_verifier")
                    else f"{record.name}:{record.lineno}:"
                )
                github.debug(other_name + record.getMessage())
            return

        if (gh := getattr(record, "github", None)) is None or not isinstance(
            gh, GitHubMessageParams
        ):
            return

        if not gh.title:
            gh.title = record.name

        github.message(command, record.getMessage(), stream=sys.stderr, **asdict(gh))


def configure_stderr_logging(
    default_level: int | None = None,
) -> None:  # pragma: no cover
    colorlog_handler = colorlog.StreamHandler(sys.stderr)
    colorlog_handler.setLevel(default_level or WARNING)
    colorlog_handler.setFormatter(
        colorlog.ColoredFormatter(
            "%(log_color)s%(levelname)s%(reset)s:%(name)s:%(lineno)d:%(message)s"
        )
    )

    handlers: list[Handler] = [colorlog_handler]

    if github.env.is_in_github_actions():
        handlers.append(GitHubActionsHandler())

    basicConfig(
        level=NOTSET,
        handlers=handlers,
    )


def _console_group(category: str, *, title: str, file: TextIO | None):
    print(
        (
            f"<------------- {Fore.CYAN}{category}:"
            f"{Fore.YELLOW}{title}"
            f"{Style.RESET_ALL} ------------->"
        ),
        file=file,
    )


@contextmanager
def group(title: str, *, stream: TextIO | None = None):
    if stream is None:
        stream = sys.stderr
    if github.env.is_in_github_actions():
        try:
            github.begin_group(title, stream=stream)
            yield
        finally:
            github.end_group(stream=stream)
    else:
        try:
            _console_group(" Start group", title=title, file=stream)
            yield
        finally:
            _console_group("Finish group", title=title, file=stream)
