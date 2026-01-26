import pathlib
from argparse import ArgumentParser
from logging import getLogger
from typing import Literal

from pydantic import Field

from competitive_verifier import config
from competitive_verifier.arg import (
    IgnoreErrorArguments,
    IncludeExcludeArguments,
    ResultJsonArguments,
    VerboseArguments,
    VerifyFilesJsonArguments,
    WriteSummaryArguments,
)
from competitive_verifier.inout import MergeResult
from competitive_verifier.models import (
    VerificationInput,
)

from .builder import DocumentBuilder

logger = getLogger(__name__)


def get_default_docs_dir() -> pathlib.Path:
    default_docs_dir = config.get_config_dir() / "docs"
    oj_verify_docs_dir = pathlib.Path(".verify-helper/docs")
    if not default_docs_dir.exists() and oj_verify_docs_dir.exists():
        return oj_verify_docs_dir
    return default_docs_dir


class Docs(
    IncludeExcludeArguments,
    WriteSummaryArguments,
    IgnoreErrorArguments,
    ResultJsonArguments,
    VerifyFilesJsonArguments,
    VerboseArguments,
):
    subcommand: Literal["docs"] = Field(
        default="docs",
        description="Create documents",
    )
    docs: pathlib.Path | None = None
    destination: pathlib.Path

    @classmethod
    def add_parser(cls, parser: ArgumentParser):
        super().add_parser(parser)
        destination = config.get_config_dir() / "_jekyll"
        parser.add_argument(
            "--docs",
            type=pathlib.Path,
            help=f"Document settings directory. default: {get_default_docs_dir().as_posix()}",
        )
        parser.add_argument(
            "--destination",
            type=pathlib.Path,
            default=destination,
            help=f"Output directory for markdown document. default: {destination.as_posix()}",
        )

    def _run(self) -> bool:
        logger.debug("arguments:%s", self)
        logger.info("verify_files_json=%s", str(self.verify_files_json))
        logger.info("result_json=%s", [str(p) for p in self.result_json])

        verifications = VerificationInput.parse_file_relative(self.verify_files_json)

        result = MergeResult(
            subcommand="merge-result",
            result_json=self.result_json,
            write_summary=self.write_summary,
        ).merge()

        logger.debug(
            "verifications=%s", verifications.model_dump_json(exclude_none=True)
        )
        logger.debug("result=%s", result.model_dump_json(exclude_none=True))

        return DocumentBuilder(
            verifications=verifications,
            result=result,
            docs_dir=self.docs or get_default_docs_dir(),
            destination_dir=self.destination,
            include=self.include,
            exclude=self.exclude,
        ).build()
