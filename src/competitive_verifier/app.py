import importlib.metadata
import logging
import pathlib
import sys
from abc import ABC, abstractmethod
from logging import getLogger
from typing import cast

from pydantic import AliasChoices, BaseModel, Field, model_validator
from pydantic_settings import (
    BaseSettings,
    CliApp,
    CliPositionalArg,
    CliSettingsSource,
    CliSubCommand,
    CliToggleFlag,
    get_subcommand,
)

from . import github, merge, summary
from .log import configure_stderr_logging

# ruff: noqa: PLC0415

COMPETITIVE_VERIFY_FILES_PATH = "COMPETITIVE_VERIFY_FILES_PATH"

LOGGING_ENABLED = True

logger = getLogger(__name__)


# Abstract Subcommands
class AbstractSubcommand(ABC, BaseModel):
    @abstractmethod
    def run(self) -> bool: ...


class VerboseSubcommand(AbstractSubcommand):
    verbose: bool = Field(
        default=False,
        validation_alias=AliasChoices("verbose", "v"),
        description="Show debug level log.",
    )

    @model_validator(mode="after")
    def init_logging(self) -> "VerboseSubcommand":
        if LOGGING_ENABLED:
            default_level = logging.INFO
            if self.verbose:
                default_level = logging.DEBUG
            configure_stderr_logging(default_level)
        return self


class ResultJsonSubcommand(AbstractSubcommand):
    result_json: CliPositionalArg[list[pathlib.Path]] = Field(
        description="Json files which is result of `verify`",
    )


class WriteSummarySubcommand(AbstractSubcommand):
    write_summary: bool = Field(
        default=False,
        description="Write GitHub Actions summary",
    )

    @property
    def gh_summary_path(self) -> pathlib.Path | None:
        """For `summary.try_write_summary(gh_summary_path, result)`."""
        if self.write_summary:
            gh_summary_path = github.env.get_step_summary_path()
            if gh_summary_path and gh_summary_path.parent.exists():
                return gh_summary_path
            logger.warning("write_summary=True but not found $GITHUB_STEP_SUMMARY")
        return None


class IncludeExcludeSubcommand(AbstractSubcommand):
    include: list[str] = Field(
        default_factory=list[str],
        description="Included file",
    )
    exclude: list[str] = Field(
        default_factory=list[str],
        description="Excluded file",
    )


# Subcommands


class MergeInput(
    VerboseSubcommand,
):
    verify_files_json: CliPositionalArg[list[pathlib.Path]] = Field(
        description="verify_files.json files",
    )

    def run(self):
        result = merge.merge_input_files(self.verify_files_json)
        print(result.model_dump_json(exclude_none=True))
        return True


class MergeResult(
    ResultJsonSubcommand,
    WriteSummarySubcommand,
    VerboseSubcommand,
):
    def run(self):
        result = merge.merge_result_files(self.result_json)
        summary.try_write_summary(self.gh_summary_path, result)
        print(result.model_dump_json(exclude_none=True))
        return True


class OjResolve(
    IncludeExcludeSubcommand,
    VerboseSubcommand,
):
    bundle: CliToggleFlag[bool] = Field(
        default=True,
        description="bundle",
    )
    config: pathlib.Path = Field(
        description="path to config.toml",
    )

    def run(self):
        print(self)
        return True


class Migrate(
    VerboseSubcommand,
):
    dry_run: bool = Field(
        default=False,
        validation_alias=AliasChoices("dry-run", "n"),
        description="Run a trial migration with no changes. Just show logs only.",
    )

    def run(self):
        from .migrate import migration

        logger.debug("arguments=%r", self)
        return migration.main(dry_run=self.dry_run)


class RootCommand(
    BaseSettings,
    cli_parse_args=True,
    cli_kebab_case=True,
    cli_implicit_flags="toggle",
):
    # verify: CliSubCommand[None] = Field(
    #     alias="verify",
    #     description="Verify library",
    # )
    # docs: CliSubCommand[None] = Field(
    #     alias="docs",
    #     description="Create documents",
    # )
    # download: CliSubCommand[None] = Field(
    #     alias="download",
    #     description="Download problems",
    # )
    merge_input: CliSubCommand[MergeInput] = Field(
        alias="merge-input",
        description="Merge verify_files.json",
    )
    merge_result: CliSubCommand[MergeResult] = Field(
        alias="merge-result",
        description="Merge result of `verify`",
    )
    # check: CliSubCommand[None] = Field(
    #     alias="check",
    #     description="Check result of `verify`",
    # )
    oj_resolve: CliSubCommand[OjResolve] = Field(
        alias="oj-resolve",
        description="Create verify_files json using `oj-verify`",
    )
    migrate: CliSubCommand[Migrate] = Field(
        description="Migration from verification-helper(`oj-verify`) project",
    )

    version: bool = Field(
        default=False,
        description="print version number",
    )

    def cli_cmd(self):
        if self.version:
            print(importlib.metadata.version("competitive-verifier"))
            return
        subcommand = cast("AbstractSubcommand", get_subcommand(self, is_required=False))
        if subcommand:
            sys.exit(0 if subcommand.run() else 1)

        CliSettingsSource(RootCommand).root_parser.print_help()  # pyright: ignore[reportUnknownMemberType]


def main(args: list[str] | None = None):
    CliApp.run(RootCommand, cli_args=args)


if __name__ == "__main__":
    main()
