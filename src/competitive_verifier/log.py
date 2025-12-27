import sys
from contextlib import contextmanager
from logging import (
    CRITICAL,
    DEBUG,
    ERROR,
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


class GitHubActionsHandler(Handler):
    def __init__(self, *, stream: TextIO | None = None) -> None:
        super().__init__(DEBUG)
        self.stream = stream

    def emit(self, record: LogRecord) -> None:
        message = record.getMessage()

        if record.levelno == DEBUG:
            github.print_debug(message, stream=self.stream)
        elif record.levelno == WARNING:
            github.print_warning(message, stream=self.stream)
        elif record.levelno in (ERROR, CRITICAL):
            github.print_error(message, stream=self.stream)


def configure_stderr_logging(default_level: int | None = None) -> None:
    colorlog_handler = colorlog.StreamHandler(sys.stderr)
    colorlog_handler.setLevel(default_level or WARNING)
    colorlog_handler.setFormatter(
        colorlog.ColoredFormatter(
            "%(log_color)s%(levelname)s%(reset)s:%(name)s:%(lineno)d:%(message)s"
        )
    )
    handlers: list[Handler] = [colorlog_handler]

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
