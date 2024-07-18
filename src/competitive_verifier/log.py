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
from typing import Optional, TextIO

import colorlog
from colorama import Fore, Style

import competitive_verifier.github as github

# _orig_stderr = sys.stderr


# def override_stderr() -> None:
#     sys.stderr = sys.stdout


# def restore_stderr() -> None:
#     sys.stderr = _orig_stderr


class GitHubActionsHandler(Handler):
    def __init__(self, *, stream: Optional[TextIO] = None) -> None:
        super().__init__(DEBUG)
        self.stream = stream

    def emit(self, record: LogRecord) -> None:
        message = record.getMessage()
        # file = record.pathname
        # line = record.levelno

        if record.levelno == DEBUG:
            github.print_debug(message, stream=self.stream)
        elif record.levelno == WARNING:
            github.print_warning(message, stream=self.stream)
        elif record.levelno == ERROR or record.levelno == CRITICAL:
            github.print_error(message, stream=self.stream)


# class ExceptGitHubActionsFilter(Filter):
#     def __init__(self) -> None:
#         super().__init__()

#     def filter(self, record: LogRecord) -> bool:
#         return (
#             record.levelno != WARNING
#             and record.levelno != ERROR
#             and record.levelno != CRITICAL
#         )


def configure_logging(
    default_level: Optional[int] = None,
    in_github_actions: Optional[bool] = None,
) -> None:
    if in_github_actions is None:
        in_github_actions = github.env.is_in_github_actions()

    # override_stderr()

    colorlog_handler = colorlog.StreamHandler()
    colorlog_handler.setLevel(default_level or WARNING)
    colorlog_handler.setFormatter(
        colorlog.ColoredFormatter(
            "%(log_color)s%(levelname)s%(reset)s:%(name)s:%(message)s"
        )
    )
    handlers: list[Handler] = [colorlog_handler]

    if in_github_actions:
        handlers.append(GitHubActionsHandler())
        # colorlog_handler.addFilter(ExceptGitHubActionsFilter())

    basicConfig(
        level=NOTSET,
        handlers=handlers,
    )


def configure_stderr_logging(default_level: Optional[int] = None) -> None:
    colorlog_handler = colorlog.StreamHandler(sys.stderr)
    colorlog_handler.setLevel(default_level or WARNING)
    colorlog_handler.setFormatter(
        colorlog.ColoredFormatter(
            "%(log_color)s%(levelname)s%(reset)s:%(name)s:%(lineno)d: %(message)s"
        )
    )
    handlers: list[Handler] = [colorlog_handler]

    basicConfig(
        level=NOTSET,
        handlers=handlers,
    )


def _console_group(category: str, *, title: str, file: Optional[TextIO]):
    print(
        (
            f"<------------- {Fore.CYAN}{category}:"
            f"{Fore.YELLOW}{title}"
            f"{Style.RESET_ALL} ------------->"
        ),
        file=file,
    )


@contextmanager
def group(title: str, *, stream: Optional[TextIO] = None):
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
