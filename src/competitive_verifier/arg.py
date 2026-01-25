import logging
import os
import pathlib
from abc import ABC, abstractmethod
from argparse import ArgumentParser
from logging import getLogger
from typing import TYPE_CHECKING, TypedDict, cast, get_args

from pydantic import BaseModel, Field

from competitive_verifier import github, summary

from .log import configure_stderr_logging

if TYPE_CHECKING:
    from competitive_verifier.models import VerifyCommandResult

COMPETITIVE_VERIFY_FILES_PATH = "COMPETITIVE_VERIFY_FILES_PATH"

logger = getLogger(__name__)


class _SubcommandInfo(TypedDict):
    name: str
    help: str | None


class BaseArguments(ABC, BaseModel):
    model_config = {"extra": "ignore"}

    @classmethod
    def get_subcommand_info(cls) -> _SubcommandInfo | None:
        f = cls.model_fields.get("subcommand")
        if f is None or (subcommand := get_args(f.annotation)[0]) is None:
            return None

        return {"name": cast("str", subcommand), "help": f.description}

    @abstractmethod
    def run(self) -> bool: ...

    @classmethod
    def add_parser(cls, parser: ArgumentParser):
        pass


class VerifyFilesJsonArgumentsMixin(BaseArguments):
    @classmethod
    def _required(cls) -> bool:
        return True

    @classmethod
    def add_parser(cls, parser: ArgumentParser):
        super().add_parser(parser)

        default = os.getenv(COMPETITIVE_VERIFY_FILES_PATH)
        parser.add_argument(
            "--verify-json",
            dest="verify_files_json",
            default=default or None,
            required=cls._required() and not bool(default),
            help="File path of verify_files.json. default: environ variable $COMPETITIVE_VERIFY_FILES_PATH",
            type=pathlib.Path,
        )


class VerifyFilesJsonArguments(VerifyFilesJsonArgumentsMixin):
    verify_files_json: pathlib.Path


class OptionalVerifyFilesJsonArguments(VerifyFilesJsonArgumentsMixin):
    verify_files_json: pathlib.Path | None

    @classmethod
    def _required(cls) -> bool:
        return False


class ResultJsonArguments(BaseArguments):
    result_json: list[pathlib.Path]

    @classmethod
    def add_parser(cls, parser: ArgumentParser):
        super().add_parser(parser)
        parser.add_argument(
            "result_json",
            nargs="+",
            help="Json files which is result of `verify`",
            type=pathlib.Path,
        )


class IgnoreErrorArguments(BaseArguments):
    ignore_error: bool = True

    @classmethod
    def add_parser(cls, parser: ArgumentParser):
        super().add_parser(parser)
        parser.add_argument(
            "--check-error",
            help="Exit not zero if failed verification exists",
            dest="ignore_error",
            action="store_false",
        )


class WriteSummaryArguments(BaseArguments):
    write_summary: bool = False

    @classmethod
    def add_parser(cls, parser: ArgumentParser):
        super().add_parser(parser)
        parser.add_argument(
            "--write-summary",
            action="store_true",
            help="Write GitHub Actions summary",
        )

    def write_result(self, result: "VerifyCommandResult"):
        if self.write_summary:
            gh_summary_path = github.env.get_step_summary_path()
            if gh_summary_path and gh_summary_path.parent.exists():
                with gh_summary_path.open("w", encoding="utf-8") as fp:
                    summary.write_summary(fp, result)
            else:
                logger.warning("write_summary=True but not found $GITHUB_STEP_SUMMARY")


class IncludeExcludeArguments(BaseArguments):
    include: list[str] = Field(default_factory=list)
    exclude: list[str] = Field(default_factory=list)

    @classmethod
    def add_parser(cls, parser: ArgumentParser):
        super().add_parser(parser)
        parser.add_argument(
            "--include",
            nargs="*",
            help="Included file",
            default=[],
            type=str,
        )
        parser.add_argument(
            "--exclude",
            nargs="*",
            help="Excluded file",
            default=[],
            type=str,
        )


class VerboseArguments(BaseArguments):
    verbose: bool = False

    @abstractmethod
    def _run(self) -> bool: ...
    def run(self) -> bool:
        default_level = logging.INFO
        if self.verbose:
            default_level = logging.DEBUG
        configure_stderr_logging(default_level)
        return self._run()

    @classmethod
    def add_parser(cls, parser: ArgumentParser):
        super().add_parser(parser)
        parser.add_argument(
            "-v", "--verbose", action="store_true", help="Show debug level log."
        )
